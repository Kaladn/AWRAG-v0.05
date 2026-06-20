#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

using Symbol6 = std::array<std::uint8_t, 6>;

constexpr const char* COPYRIGHT = "Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved.";
constexpr const char* WATERMARK = "AWRAG public-review facsimile output; not source evidence. Verify against cited source coordinates.";
constexpr const char* LICENSE_REF = "AWRAG Public Review License";
constexpr const char* FACSIMILE_WARNING = "This output is a local processing facsimile, not source evidence or professional advice.";
constexpr const char* COUNT_BACKEND = "awrag_native_binary_counts@1";
constexpr const char* COMPUTE_ENGINE = "awrag_native_cpp_counts@1";
constexpr const char* SYMBOL_SYSTEM = "awrag_public_6b@1";
constexpr int SYMBOL_BYTES = 6;
constexpr int MAX_BLOCK_LINES = 40;
constexpr int ANCHOR_RECORD_SIZE = 14;
constexpr int RELATION_RECORD_SIZE = 18;
constexpr int BLOCK_ANCHOR_RECORD_SIZE = 12;

struct Paths {
    fs::path root;
    fs::path incoming;
    fs::path state;
    fs::path counts;
    fs::path coordinates;
    fs::path citations;
    fs::path outputs;
    fs::path receipts;
    fs::path anchor_counts;
    fs::path relation_counts;
    fs::path block_anchor_postings;
    fs::path blocks;
    fs::path lexicon;
    fs::path manifest;
    fs::path chat_metadata;
};

struct Block {
    int ordinal = 0;
    std::string block_id;
    std::string file_path;
    int line_start = 0;
    int line_end = 0;
    std::string text;
    std::string citation_id;
    std::string marker;
    std::string text_hash;
    std::map<std::string, std::string> chat;
};

struct Candidate {
    int block = 0;
    double score = 0.0;
    double density = 0.0;
    int anchor_count = 1;
    int direct_hits = 0;
    std::set<std::string> matched;
    std::set<std::string> direct_matched;
};

std::string arg_value(int argc, char** argv, const std::string& name) {
    for (int i = 2; i + 1 < argc; ++i) {
        if (argv[i] == name) return argv[i + 1];
    }
    throw std::runtime_error("missing required argument: " + name);
}

std::string optional_arg(int argc, char** argv, const std::string& name, const std::string& fallback = "") {
    for (int i = 2; i + 1 < argc; ++i) {
        if (argv[i] == name) return argv[i + 1];
    }
    return fallback;
}

int optional_int(int argc, char** argv, const std::string& name, int fallback) {
    const auto text = optional_arg(argc, argv, name, "");
    return text.empty() ? fallback : std::stoi(text);
}

std::string lower(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return value;
}

std::string trim(const std::string& value) {
    std::size_t start = 0;
    while (start < value.size() && std::isspace(static_cast<unsigned char>(value[start]))) ++start;
    std::size_t end = value.size();
    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1]))) --end;
    return value.substr(start, end - start);
}

std::string safe_id(const std::string& value) {
    std::string out;
    for (char ch : value) {
        if (std::isalnum(static_cast<unsigned char>(ch)) || ch == '_' || ch == '.' || ch == '-') out.push_back(ch);
        else out.push_back('_');
    }
    while (!out.empty() && (out.front() == '.' || out.front() == '_')) out.erase(out.begin());
    while (!out.empty() && (out.back() == '.' || out.back() == '_')) out.pop_back();
    if (out.empty()) throw std::runtime_error("dataset id is required");
    return out;
}

std::string json_escape(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 8);
    for (unsigned char ch : value) {
        switch (ch) {
            case '\\': out += "\\\\"; break;
            case '"': out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            default:
                if (ch < 0x20) out += ' ';
                else out.push_back(static_cast<char>(ch));
        }
    }
    return out;
}

std::string now_stamp() {
    const auto now = std::chrono::system_clock::now();
    const auto t = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
#ifdef _WIN32
    gmtime_s(&tm, &t);
#else
    gmtime_r(&t, &tm);
#endif
    std::ostringstream out;
    out << std::put_time(&tm, "%Y%m%dT%H%M%SZ");
    return out.str();
}

std::uint64_t fnv1a64(const std::string& text) {
    std::uint64_t hash = 14695981039346656037ULL;
    for (unsigned char ch : text) {
        hash ^= static_cast<std::uint64_t>(ch);
        hash *= 1099511628211ULL;
    }
    return hash;
}

std::string hex64(std::uint64_t value) {
    std::ostringstream out;
    out << std::hex << std::setfill('0') << std::setw(16) << std::nouppercase << value;
    return out.str();
}

Symbol6 symbol_for_anchor(const std::string& anchor) {
    const auto hash = fnv1a64(anchor);
    Symbol6 symbol{};
    for (int i = 0; i < 6; ++i) {
        symbol[static_cast<std::size_t>(5 - i)] = static_cast<std::uint8_t>((hash >> (i * 8)) & 0xff);
    }
    return symbol;
}

std::string symbol_hex(const Symbol6& symbol) {
    std::ostringstream out;
    out << "0x" << std::uppercase << std::hex << std::setfill('0');
    for (auto byte : symbol) out << std::setw(2) << static_cast<int>(byte);
    return out.str();
}

void write_u16_be(std::ofstream& out, std::int16_t value) {
    const auto raw = static_cast<std::uint16_t>(value);
    char bytes[2] = {
        static_cast<char>((raw >> 8) & 0xff),
        static_cast<char>(raw & 0xff),
    };
    out.write(bytes, 2);
}

void write_u32_be(std::ofstream& out, std::uint32_t value) {
    char bytes[4] = {
        static_cast<char>((value >> 24) & 0xff),
        static_cast<char>((value >> 16) & 0xff),
        static_cast<char>((value >> 8) & 0xff),
        static_cast<char>(value & 0xff),
    };
    out.write(bytes, 4);
}

void write_u64_be(std::ofstream& out, std::uint64_t value) {
    char bytes[8] = {};
    for (int i = 0; i < 8; ++i) bytes[i] = static_cast<char>((value >> ((7 - i) * 8)) & 0xff);
    out.write(bytes, 8);
}

std::uint16_t read_u16_be(const std::vector<unsigned char>& data, std::size_t offset) {
    return static_cast<std::uint16_t>((data[offset] << 8) | data[offset + 1]);
}

std::uint32_t read_u32_be(const std::vector<unsigned char>& data, std::size_t offset) {
    return (static_cast<std::uint32_t>(data[offset]) << 24) |
           (static_cast<std::uint32_t>(data[offset + 1]) << 16) |
           (static_cast<std::uint32_t>(data[offset + 2]) << 8) |
           static_cast<std::uint32_t>(data[offset + 3]);
}

std::uint64_t read_u64_be(const std::vector<unsigned char>& data, std::size_t offset) {
    std::uint64_t value = 0;
    for (int i = 0; i < 8; ++i) value = (value << 8) | data[offset + i];
    return value;
}

std::vector<unsigned char> read_binary(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

std::string read_text(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("cannot read: " + path.string());
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

void write_text(const fs::path& path, const std::string& text) {
    fs::create_directories(path.parent_path());
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) throw std::runtime_error("cannot write: " + path.string());
    out << text;
}

std::string protected_prefix() {
    std::ostringstream out;
    out << "\"copyright\":\"" << json_escape(COPYRIGHT) << "\","
        << "\"owner\":\"Cortex Evolved Systems\","
        << "\"license\":\"" << LICENSE_REF << "\","
        << "\"watermark\":\"" << json_escape(WATERMARK) << "\","
        << "\"facsimile_warning\":\"" << json_escape(FACSIMILE_WARNING) << "\","
        << "\"watermark_locked\":true,"
        << "\"removal_prohibited\":true,";
    return out.str();
}

std::string protected_object(const std::string& body) {
    return "{" + protected_prefix() + body + "}";
}

Paths paths_for(const fs::path& runtime_root, const std::string& dataset_id) {
    Paths paths;
    paths.root = fs::absolute(runtime_root) / "datasets" / safe_id(dataset_id);
    paths.incoming = paths.root / "incoming";
    paths.state = paths.root / "state";
    paths.counts = paths.root / "counts";
    paths.coordinates = paths.root / "coordinates";
    paths.citations = paths.root / "citations";
    paths.outputs = paths.root / "outputs";
    paths.receipts = paths.root / "receipts";
    paths.anchor_counts = paths.counts / "anchor_counts.awbin";
    paths.relation_counts = paths.counts / "relation_counts.awbin";
    paths.block_anchor_postings = paths.counts / "block_anchor_postings.awbin";
    paths.blocks = paths.state / "blocks.jsonl";
    paths.lexicon = paths.state / "dataset_lexicon.json";
    paths.manifest = paths.root / "dataset_manifest.json";
    paths.chat_metadata = paths.state / "chat_metadata_index.jsonl";
    return paths;
}

void ensure_dirs(const Paths& paths) {
    for (const auto& path : {paths.root, paths.incoming, paths.state, paths.counts, paths.coordinates, paths.citations, paths.outputs, paths.receipts}) {
        fs::create_directories(path);
    }
}

std::uint64_t record_count(const fs::path& path, int size) {
    if (!fs::exists(path)) return 0;
    return static_cast<std::uint64_t>(fs::file_size(path) / static_cast<std::uint64_t>(size));
}

std::uint64_t jsonl_count(const fs::path& path) {
    if (!fs::exists(path)) return 0;
    std::ifstream in(path, std::ios::binary);
    std::uint64_t count = 0;
    std::string line;
    while (std::getline(in, line)) {
        if (!trim(line).empty()) ++count;
    }
    return count;
}

const std::set<std::string>& stop_anchors() {
    static const std::set<std::string> stops = {
        "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
        "doc", "docs", "document", "documents", "explain", "explained", "explains",
        "file", "files", "for", "from", "how", "in", "into", "is", "it", "of", "on",
        "or", "project", "say", "said", "says", "mention", "mentioned", "mentions",
        "that", "the", "this", "to", "what", "where", "which", "who", "why", "with"
    };
    return stops;
}

std::string normalize_anchor(std::string value) {
    value = lower(trim(value));
    if (value.size() > 4 && value.substr(value.size() - 3) == "ies") return value.substr(0, value.size() - 3) + "y";
    if (value.size() > 3 && value.back() == 's' && !(value.size() >= 2 && value.substr(value.size() - 2) == "ss")) return value.substr(0, value.size() - 1);
    return value;
}

std::vector<std::string> anchorize(const std::string& text) {
    static const std::regex word_re("[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?");
    std::vector<std::string> anchors;
    for (auto it = std::sregex_iterator(text.begin(), text.end(), word_re); it != std::sregex_iterator(); ++it) {
        auto value = normalize_anchor((*it).str());
        if (value.empty() || stop_anchors().count(value)) continue;
        anchors.push_back(value);
    }
    return anchors;
}

std::vector<std::string> expand_query_anchors(const std::vector<std::string>& anchors) {
    std::vector<std::string> out;
    std::set<std::string> seen;
    for (const auto& anchor : anchors) {
        std::vector<std::string> variants{anchor, normalize_anchor(anchor)};
        bool alpha = !anchor.empty() && std::all_of(anchor.begin(), anchor.end(), [](unsigned char ch) { return std::isalpha(ch); });
        if (alpha && anchor.size() > 2) variants.push_back(anchor + "s");
        for (const auto& variant : variants) {
            if (!variant.empty() && !stop_anchors().count(variant) && seen.insert(variant).second) out.push_back(variant);
        }
    }
    return out;
}

std::vector<fs::path> iter_files(const fs::path& source) {
    const std::set<std::string> suffixes = {".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".jsonl"};
    std::vector<fs::path> files;
    if (fs::is_regular_file(source) && suffixes.count(lower(source.extension().string()))) {
        files.push_back(fs::absolute(source));
    } else if (fs::is_directory(source)) {
        for (const auto& item : fs::recursive_directory_iterator(source)) {
            if (!item.is_regular_file()) continue;
            if (suffixes.count(lower(item.path().extension().string()))) files.push_back(fs::absolute(item.path()));
        }
    }
    std::sort(files.begin(), files.end());
    return files;
}

std::vector<std::string> split_lines(const std::string& text) {
    std::vector<std::string> lines;
    std::string current;
    for (char ch : text) {
        if (ch == '\r') continue;
        if (ch == '\n') {
            lines.push_back(current);
            current.clear();
        } else {
            current.push_back(ch);
        }
    }
    lines.push_back(current);
    return lines;
}

std::vector<Block> split_blocks(const fs::path& file, int& next_ordinal) {
    const auto text = read_text(file);
    const auto lines = split_lines(text);
    std::vector<Block> blocks;
    std::vector<std::string> current;
    int start = 1;
    const auto flush = [&](int end_line) {
        if (current.empty()) return;
        for (std::size_t offset = 0; offset < current.size(); offset += MAX_BLOCK_LINES) {
            const auto take = std::min<std::size_t>(MAX_BLOCK_LINES, current.size() - offset);
            std::ostringstream body;
            for (std::size_t i = 0; i < take; ++i) {
                if (i) body << "\n";
                body << current[offset + i];
            }
            Block block;
            block.ordinal = next_ordinal++;
            block.file_path = fs::absolute(file).string();
            block.line_start = start + static_cast<int>(offset);
            block.line_end = start + static_cast<int>(offset + take - 1);
            block.text = body.str();
            block.block_id = hex64(fnv1a64(block.file_path + ":" + std::to_string(block.line_start) + ":" + block.text));
            block.citation_id = "AWCIT-" + hex64(fnv1a64(block.block_id)).substr(0, 10);
            block.marker = "[" + block.citation_id + "]";
            block.text_hash = hex64(fnv1a64(block.text));
            blocks.push_back(block);
        }
        current.clear();
        (void)end_line;
    };
    for (std::size_t i = 0; i < lines.size(); ++i) {
        if (!trim(lines[i]).empty()) {
            if (current.empty()) start = static_cast<int>(i + 1);
            current.push_back(lines[i]);
        } else {
            flush(static_cast<int>(i));
        }
    }
    flush(static_cast<int>(lines.size()));
    return blocks;
}

std::map<std::string, std::string> parse_chat_metadata(const std::string& text) {
    std::map<std::string, std::string> meta;
    const auto lines = split_lines(text);
    for (const auto& line : lines) {
        const auto pos = line.find(':');
        if (pos == std::string::npos) continue;
        auto key = lower(trim(line.substr(0, pos)));
        auto value = trim(line.substr(pos + 1));
        if (key == "chat_conversation_id") meta["conversation_id"] = value;
        else if (key == "chat_message_id") meta["message_id"] = value;
        else if (key == "chat_title") meta["title"] = value;
        else if (key == "chat_created_at") {
            meta["created_at"] = value;
            std::smatch m;
            if (std::regex_search(value, m, std::regex("([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"))) {
                std::ostringstream date;
                date << m[3].str() << "-" << std::setw(2) << std::setfill('0') << std::stoi(m[1].str())
                     << "-" << std::setw(2) << std::setfill('0') << std::stoi(m[2].str());
                meta["date"] = date.str();
            } else if (std::regex_search(value, m, std::regex("([0-9]{4}-[0-9]{2}-[0-9]{2})"))) {
                meta["date"] = m[1].str();
            }
        } else if (key == "chat_speaker") meta["speaker"] = lower(value);
        else if (key == "chat_lifetime_allowed") meta["lifetime_allowed"] = lower(value);
        else if (key == "chat_truth_scope") meta["truth_scope"] = value;
    }
    return meta;
}

std::string array_strings(const std::vector<std::string>& values) {
    std::ostringstream out;
    out << "[";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) out << ",";
        out << "\"" << json_escape(values[i]) << "\"";
    }
    out << "]";
    return out.str();
}

std::string set_strings(const std::set<std::string>& values) {
    return array_strings(std::vector<std::string>(values.begin(), values.end()));
}

std::string block_json(const Block& b) {
    std::ostringstream out;
    out << "{\"block_ordinal\":" << b.ordinal
        << ",\"block_id\":\"" << json_escape(b.block_id) << "\""
        << ",\"file_path\":\"" << json_escape(b.file_path) << "\""
        << ",\"line_start\":" << b.line_start
        << ",\"line_end\":" << b.line_end
        << ",\"text\":\"" << json_escape(b.text) << "\""
        << ",\"citation_id\":\"" << b.citation_id << "\""
        << ",\"marker\":\"" << b.marker << "\""
        << ",\"text_hash\":\"" << b.text_hash << "\"";
    if (!b.chat.empty()) {
        out << ",\"chat_metadata\":{";
        bool first = true;
        for (const auto& [k, v] : b.chat) {
            if (!first) out << ",";
            first = false;
            if (k == "lifetime_allowed") out << "\"" << k << "\":" << (v == "true" ? "true" : "false");
            else out << "\"" << k << "\":\"" << json_escape(v) << "\"";
        }
        out << "}";
    }
    out << "}";
    return out.str();
}

std::string object_value(const std::string& object, const std::string& key) {
    const std::regex pattern("\"" + key + "\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");
    std::smatch match;
    if (!std::regex_search(object, match, pattern)) return "";
    auto raw = match[1].str();
    std::string out;
    for (std::size_t i = 0; i < raw.size(); ++i) {
        if (raw[i] == '\\' && i + 1 < raw.size()) {
            const char e = raw[++i];
            if (e == 'n') out.push_back('\n');
            else if (e == 't') out.push_back('\t');
            else out.push_back(e);
        } else {
            out.push_back(raw[i]);
        }
    }
    return out;
}

int object_int(const std::string& object, const std::string& key) {
    const std::regex pattern("\"" + key + "\"\\s*:\\s*([0-9]+)");
    std::smatch match;
    if (!std::regex_search(object, match, pattern)) return 0;
    return std::stoi(match[1].str());
}

std::vector<Block> read_blocks(const Paths& paths) {
    std::vector<Block> blocks;
    std::ifstream in(paths.blocks, std::ios::binary);
    std::string line;
    while (std::getline(in, line)) {
        if (trim(line).empty()) continue;
        Block b;
        b.ordinal = object_int(line, "block_ordinal");
        b.block_id = object_value(line, "block_id");
        b.file_path = object_value(line, "file_path");
        b.line_start = object_int(line, "line_start");
        b.line_end = object_int(line, "line_end");
        b.text = object_value(line, "text");
        b.citation_id = object_value(line, "citation_id");
        b.marker = object_value(line, "marker");
        b.text_hash = object_value(line, "text_hash");
        b.chat["date"] = object_value(line, "date");
        b.chat["speaker"] = object_value(line, "speaker");
        blocks.push_back(b);
    }
    return blocks;
}

void write_manifest(const Paths& paths, const std::string& dataset_id, const std::string& owner) {
    std::ostringstream out;
    out << protected_object(
        "\"schema\":\"awrag_dataset_manifest@1\","
        "\"created_at\":\"" + now_stamp() + "\","
        "\"dataset_id\":\"" + json_escape(safe_id(dataset_id)) + "\","
        "\"dataset_owner\":\"" + json_escape(owner) + "\","
        "\"scope\":\"dataset_local\","
        "\"rag_allowed\":true,"
        "\"promotion_allowed\":false,"
        "\"global_training_allowed\":false,"
        "\"delete_with_dataset\":true,"
        "\"counts_are_memory\":false,"
        "\"counts_belong_to\":\"dataset\","
        "\"count_backend\":\"" + std::string(COUNT_BACKEND) + "\","
        "\"compute_engine\":\"" + std::string(COMPUTE_ENGINE) + "\","
        "\"symbol_system\":\"" + std::string(SYMBOL_SYSTEM) + "\","
        "\"symbol_bytes\":6,"
        "\"symbol_scope\":\"dataset_local_demo_only\","
        "\"symbol_transferable\":false,"
        "\"anchorworks_lifetime_symbol_compatible\":false"
    );
    write_text(paths.manifest, out.str() + "\n");
}

void ensure_dataset(const fs::path& runtime_root, const std::string& dataset_id, const std::string& owner) {
    const auto paths = paths_for(runtime_root, dataset_id);
    ensure_dirs(paths);
    if (!fs::exists(paths.manifest)) write_manifest(paths, dataset_id, owner);
    if (!fs::exists(paths.blocks)) write_text(paths.blocks, "");
    if (!fs::exists(paths.chat_metadata)) write_text(paths.chat_metadata, "");
    if (!fs::exists(paths.anchor_counts)) write_text(paths.anchor_counts, "");
    if (!fs::exists(paths.relation_counts)) write_text(paths.relation_counts, "");
    if (!fs::exists(paths.block_anchor_postings)) write_text(paths.block_anchor_postings, "");
}

void write_counts(const Paths& paths, const std::map<std::string, std::uint64_t>& anchors,
                  const std::map<std::tuple<std::string, std::string, int>, std::uint32_t>& relations,
                  const std::vector<std::tuple<std::string, int, int>>& postings) {
    {
        std::ofstream out(paths.anchor_counts, std::ios::binary | std::ios::trunc);
        for (const auto& [anchor, count] : anchors) {
            const auto symbol = symbol_for_anchor(anchor);
            out.write(reinterpret_cast<const char*>(symbol.data()), 6);
            write_u64_be(out, count);
        }
    }
    {
        std::ofstream out(paths.relation_counts, std::ios::binary | std::ios::trunc);
        for (const auto& [key, count] : relations) {
            const auto a = symbol_for_anchor(std::get<0>(key));
            const auto b = symbol_for_anchor(std::get<1>(key));
            out.write(reinterpret_cast<const char*>(a.data()), 6);
            out.write(reinterpret_cast<const char*>(b.data()), 6);
            write_u16_be(out, static_cast<std::int16_t>(std::get<2>(key)));
            write_u32_be(out, count);
        }
    }
    auto sorted = postings;
    std::sort(sorted.begin(), sorted.end(), [](const auto& left, const auto& right) {
        const auto ls = symbol_hex(symbol_for_anchor(std::get<0>(left)));
        const auto rs = symbol_hex(symbol_for_anchor(std::get<0>(right)));
        if (ls != rs) return ls < rs;
        if (std::get<1>(left) != std::get<1>(right)) return std::get<1>(left) < std::get<1>(right);
        return std::get<2>(left) < std::get<2>(right);
    });
    {
        std::ofstream out(paths.block_anchor_postings, std::ios::binary | std::ios::trunc);
        for (const auto& [anchor, block, pos] : sorted) {
            const auto symbol = symbol_for_anchor(anchor);
            out.write(reinterpret_cast<const char*>(symbol.data()), 6);
            write_u32_be(out, static_cast<std::uint32_t>(block));
            write_u16_be(out, static_cast<std::uint16_t>(pos));
        }
    }
}

std::map<std::string, std::string> read_symbol_to_anchor(const Paths& paths) {
    std::map<std::string, std::string> rows;
    if (!fs::exists(paths.lexicon)) return rows;
    const auto text = read_text(paths.lexicon);
    const std::regex row_re("\\{[^{}]*\"anchor\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"[^{}]*\"symbol\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), row_re); it != std::sregex_iterator(); ++it) {
        rows[(*it)[2].str()] = (*it)[1].str();
    }
    return rows;
}

void write_lexicon(const Paths& paths, const std::string& dataset_id, const std::map<std::string, std::uint64_t>& anchors) {
    std::ostringstream out;
    out << "{" << protected_prefix()
        << "\"schema\":\"awrag_dataset_lexicon@1\","
        << "\"dataset_id\":\"" << json_escape(safe_id(dataset_id)) << "\","
        << "\"scope\":\"dataset_local\","
        << "\"symbol_system\":\"" << SYMBOL_SYSTEM << "\","
        << "\"symbol_bytes\":6,"
        << "\"symbol_scope\":\"dataset_local_demo_only\","
        << "\"symbol_transferable\":false,"
        << "\"lifetime_allowed\":false,"
        << "\"anchorworks_lifetime_symbol_compatible\":false,"
        << "\"anchor_count\":" << anchors.size() << ",\"anchors\":[";
    bool first = true;
    std::map<std::string, std::string> seen;
    for (const auto& [anchor, count] : anchors) {
        const auto sym = symbol_hex(symbol_for_anchor(anchor));
        const auto old = seen.find(sym);
        if (old != seen.end() && old->second != anchor) throw std::runtime_error("symbol collision in dataset-local public namespace");
        seen[sym] = anchor;
        if (!first) out << ",";
        first = false;
        out << "{\"anchor\":\"" << json_escape(anchor) << "\",\"symbol\":\"" << sym
            << "\",\"symbol_system\":\"" << SYMBOL_SYSTEM << "\",\"symbol_bytes\":6,\"observations\":" << count
            << ",\"scope\":\"dataset_local\",\"symbol_scope\":\"dataset_local_demo_only\","
            << "\"transferable\":false,\"lifetime_allowed\":false,"
            << "\"anchorworks_lifetime_symbol_compatible\":false,\"promotion_allowed\":false}";
    }
    out << "]}";
    write_text(paths.lexicon, out.str() + "\n");
}

std::string location_json(const Block& b, double score, double density, int direct, int anchor_count,
                          const std::set<std::string>& matched, const std::set<std::string>& direct_matched,
                          const std::string& qualification = "") {
    std::ostringstream out;
    out << "{\"citation\":\"" << b.marker << "\","
        << "\"file_path\":\"" << json_escape(b.file_path) << "\","
        << "\"line_start\":" << b.line_start << ",\"line_end\":" << b.line_end << ","
        << "\"score\":" << std::fixed << std::setprecision(4) << score << ","
        << "\"density_score\":" << density << ","
        << "\"block_anchor_count\":" << anchor_count << ","
        << "\"direct_hit_count\":" << direct << ","
        << "\"direct_matched_anchors\":" << set_strings(direct_matched) << ","
        << "\"matched_anchors\":" << set_strings(matched) << ","
        << "\"text\":\"" << json_escape(b.text) << "\"";
    if (!qualification.empty()) out << ",\"qualification\":" << qualification;
    out << "}";
    return out.str();
}

std::string best_sentence(const std::string& text, const std::vector<std::string>& q) {
    const auto parts = split_lines(text);
    std::string best = trim(text);
    int best_score = -1;
    for (const auto& line : parts) {
        const auto low = lower(line);
        int score = 0;
        for (const auto& term : q) if (low.find(term) != std::string::npos) ++score;
        if (score > best_score && !trim(line).empty()) {
            best_score = score;
            best = trim(line);
        }
    }
    return best;
}

std::string final_answer_json(const std::vector<Block>& locations, const std::vector<std::string>& q) {
    if (locations.empty()) {
        return "{\"schema\":\"awrag_nlp_answer@1\",\"resolver\":\"awrag_deterministic_nlp_resolver@1\",\"status\":\"not_enough_information\",\"text\":\"Not enough information is available in the admitted dataset to answer this question.\",\"citations\":[],\"model_used\":\"none\",\"model_may_search\":false,\"citation_source\":\"awrag_locked_packet\"}";
    }
    std::ostringstream text;
    std::vector<std::string> citations;
    for (std::size_t i = 0; i < locations.size() && i < 3; ++i) {
        if (i) text << " ";
        auto sentence = best_sentence(locations[i].text, q);
        text << json_escape(sentence) << " " << locations[i].marker;
        citations.push_back(locations[i].marker);
    }
    std::ostringstream out;
    out << "{\"schema\":\"awrag_nlp_answer@1\",\"resolver\":\"awrag_deterministic_nlp_resolver@1\","
        << "\"status\":\"answered_from_awrag_locations\",\"text\":\"" << text.str() << "\","
        << "\"citations\":" << array_strings(citations) << ",\"model_used\":\"none\","
        << "\"model_may_search\":false,\"citation_source\":\"awrag_locked_packet\"}";
    return out.str();
}

std::string forensic_json(const std::vector<Block>& locations) {
    if (locations.empty()) {
        return "{\"schema\":\"awrag_forensic_support_receipt@1\",\"mode\":\"reconstructive_not_accusatory\",\"support_level\":\"insufficient\",\"ladder_hits\":[],\"supported\":[],\"not_supported\":[\"artifact_or_subject_referenced\"],\"citations\":[],\"conclusion\":\"The admitted record is insufficient.\"}";
    }
    std::vector<std::string> citations;
    bool deletion = false;
    bool deployment = false;
    for (const auto& b : locations) {
        citations.push_back(b.marker);
        const auto low = lower(b.text);
        if (low.find("deleted") != std::string::npos || low.find("rejected") != std::string::npos) deletion = true;
        if (low.find("deployed") != std::string::npos || low.find("executed") != std::string::npos) deployment = true;
    }
    std::vector<std::string> hits{"L1"};
    std::vector<std::string> supported{"artifact_or_subject_referenced"};
    std::vector<std::string> not_supported;
    if (deletion) {
        hits.push_back("L6");
        supported.push_back("deletion_or_rejection_discussed");
    }
    if (deployment) {
        hits.push_back("L9");
        supported.push_back("execution_or_deployment_evidenced");
    } else {
        not_supported.push_back("execution_or_deployment_evidenced");
    }
    std::ostringstream out;
    out << "{\"schema\":\"awrag_forensic_support_receipt@1\",\"mode\":\"reconstructive_not_accusatory\","
        << "\"support_level\":\"partial\",\"ladder_hits\":" << array_strings(hits)
        << ",\"supported\":" << array_strings(supported)
        << ",\"not_supported\":" << array_strings(not_supported)
        << ",\"citations\":" << array_strings(citations)
        << ",\"conclusion\":\"The record supports limited reconstruction from admitted citations.\"}";
    return out.str();
}

int cmd_init(int argc, char** argv) {
    const auto runtime = fs::path(arg_value(argc, argv, "--runtime-root"));
    const auto dataset = arg_value(argc, argv, "--dataset-id");
    const auto owner = optional_arg(argc, argv, "--owner", "operator_defined");
    ensure_dataset(runtime, dataset, owner);
    return 0;
}

std::string status_json(const fs::path& runtime, const std::string& dataset) {
    const auto paths = paths_for(runtime, dataset);
    ensure_dataset(runtime, dataset, "operator_defined");
    std::ostringstream out;
    out << protected_object(
        "\"schema\":\"awrag_dataset_status@1\","
        "\"dataset_id\":\"" + json_escape(safe_id(dataset)) + "\","
        "\"scope\":\"dataset_local\","
        "\"dataset_root\":\"" + json_escape(paths.root.string()) + "\","
        "\"count_backend\":\"" + std::string(COUNT_BACKEND) + "\","
        "\"compute_engine\":\"" + std::string(COMPUTE_ENGINE) + "\","
        "\"anchor_counts_path\":\"" + json_escape(paths.anchor_counts.string()) + "\","
        "\"relation_counts_path\":\"" + json_escape(paths.relation_counts.string()) + "\","
        "\"block_anchor_postings_path\":\"" + json_escape(paths.block_anchor_postings.string()) + "\","
        "\"dataset_lexicon_path\":\"" + json_escape(paths.lexicon.string()) + "\","
        "\"anchor_count\":" + std::to_string(record_count(paths.anchor_counts, ANCHOR_RECORD_SIZE)) + ","
        "\"relation_count\":" + std::to_string(record_count(paths.relation_counts, RELATION_RECORD_SIZE)) + ","
        "\"block_anchor_posting_count\":" + std::to_string(record_count(paths.block_anchor_postings, BLOCK_ANCHOR_RECORD_SIZE)) + ","
        "\"block_count\":" + std::to_string(jsonl_count(paths.blocks)) + ","
        "\"citation_count\":" + std::to_string(jsonl_count(paths.citations / "citations.jsonl")) + ","
        "\"chat_metadata_row_count\":" + std::to_string(jsonl_count(paths.chat_metadata)) + ","
        "\"chat_metadata_index_path\":\"" + json_escape(paths.chat_metadata.string()) + "\","
        "\"persistent_memory\":false"
    );
    return out.str();
}

int cmd_status(int argc, char** argv) {
    std::cout << status_json(fs::path(arg_value(argc, argv, "--runtime-root")), arg_value(argc, argv, "--dataset-id")) << "\n";
    return 0;
}

int cmd_intake(int argc, char** argv) {
    const auto runtime = fs::path(arg_value(argc, argv, "--runtime-root"));
    const auto dataset = arg_value(argc, argv, "--dataset-id");
    const auto source = fs::path(arg_value(argc, argv, "--source"));
    const auto owner = optional_arg(argc, argv, "--owner", "operator_defined");
    const int window = optional_int(argc, argv, "--window", 6);
    ensure_dataset(runtime, dataset, owner);
    const auto paths = paths_for(runtime, dataset);
    const auto files = iter_files(source);
    if (files.empty()) throw std::runtime_error("no intake files found");

    std::vector<Block> blocks;
    std::map<std::string, std::uint64_t> anchor_counts;
    std::map<std::tuple<std::string, std::string, int>, std::uint32_t> relation_counts;
    std::vector<std::tuple<std::string, int, int>> postings;
    int next = 0;
    std::uint64_t relation_total = 0;
    std::map<std::string, std::string> active_chat;
    for (const auto& file : files) {
        auto file_blocks = split_blocks(file, next);
        for (auto& block : file_blocks) {
            auto parsed = parse_chat_metadata(block.text);
            if (!parsed.empty()) active_chat = parsed;
            if (!active_chat.empty()) block.chat = active_chat;
            const auto anchors = anchorize(block.text);
            for (std::size_t pos = 0; pos < anchors.size(); ++pos) {
                anchor_counts[anchors[pos]] += 1;
                postings.emplace_back(anchors[pos], block.ordinal, static_cast<int>(pos));
                for (int offset = -window; offset <= window; ++offset) {
                    if (offset == 0) continue;
                    const auto n = static_cast<int>(pos) + offset;
                    if (n >= 0 && n < static_cast<int>(anchors.size())) {
                        relation_counts[std::make_tuple(anchors[pos], anchors[static_cast<std::size_t>(n)], offset)] += 1;
                        relation_total += 1;
                    }
                }
            }
            blocks.push_back(block);
        }
    }

    write_counts(paths, anchor_counts, relation_counts, postings);
    write_lexicon(paths, dataset, anchor_counts);
    {
        std::ostringstream out;
        for (const auto& b : blocks) out << block_json(b) << "\n";
        write_text(paths.blocks, out.str());
    }
    {
        std::ostringstream out;
        for (const auto& b : blocks) {
            out << protected_object("\"schema\":\"awrag_citation@1\",\"citation_id\":\"" + b.citation_id +
                "\",\"marker\":\"" + b.marker + "\",\"file_path\":\"" + json_escape(b.file_path) +
                "\",\"line_start\":" + std::to_string(b.line_start) + ",\"line_end\":" + std::to_string(b.line_end) +
                ",\"text_hash\":\"" + b.text_hash + "\",\"scope\":\"dataset_local\"") << "\n";
        }
        write_text(paths.citations / "citations.jsonl", out.str());
    }
    {
        std::ostringstream out;
        for (const auto& b : blocks) {
            out << protected_object("\"schema\":\"awrag_coordinate@1\",\"block_id\":\"" + b.block_id +
                "\",\"file_path\":\"" + json_escape(b.file_path) + "\",\"line_start\":" + std::to_string(b.line_start) +
                ",\"line_end\":" + std::to_string(b.line_end) + ",\"citation_id\":\"" + b.citation_id +
                "\",\"scope\":\"dataset_local\"") << "\n";
        }
        write_text(paths.coordinates / "coordinate_index.jsonl", out.str());
    }
    {
        std::ostringstream out;
        for (const auto& b : blocks) {
            if (b.chat.empty()) continue;
            out << protected_object("\"schema\":\"awrag_chat_metadata_index_row@1\",\"dataset_id\":\"" + safe_id(dataset) +
                "\",\"scope\":\"dataset_local\",\"block_ordinal\":" + std::to_string(b.ordinal) +
                ",\"block_id\":\"" + b.block_id + "\",\"citation_id\":\"" + b.citation_id +
                "\",\"marker\":\"" + b.marker + "\",\"file_path\":\"" + json_escape(b.file_path) +
                "\",\"line_start\":" + std::to_string(b.line_start) + ",\"line_end\":" + std::to_string(b.line_end) +
                ",\"conversation_id\":\"" + json_escape(b.chat.count("conversation_id") ? b.chat.at("conversation_id") : "") +
                "\",\"message_id\":\"" + json_escape(b.chat.count("message_id") ? b.chat.at("message_id") : "") +
                "\",\"title\":\"" + json_escape(b.chat.count("title") ? b.chat.at("title") : "") +
                "\",\"created_at\":\"" + json_escape(b.chat.count("created_at") ? b.chat.at("created_at") : "") +
                "\",\"date\":\"" + json_escape(b.chat.count("date") ? b.chat.at("date") : "") +
                "\",\"speaker\":\"" + json_escape(b.chat.count("speaker") ? b.chat.at("speaker") : "") +
                "\",\"truth_scope\":\"" + json_escape(b.chat.count("truth_scope") ? b.chat.at("truth_scope") : "") +
                "\",\"lifetime_allowed\":" + std::string((b.chat.count("lifetime_allowed") && b.chat.at("lifetime_allowed") == "true") ? "true" : "false")) << "\n";
        }
        write_text(paths.chat_metadata, out.str());
    }

    std::ostringstream receipt;
    receipt << protected_object(
        "\"schema\":\"awrag_intake_receipt@1\","
        "\"created_at\":\"" + now_stamp() + "\","
        "\"dataset_id\":\"" + safe_id(dataset) + "\","
        "\"scope\":\"dataset_local\","
        "\"source\":\"" + json_escape(fs::absolute(source).string()) + "\","
        "\"source_file_count\":" + std::to_string(files.size()) + ","
        "\"block_count\":" + std::to_string(blocks.size()) + ","
        "\"citation_count\":" + std::to_string(blocks.size()) + ","
        "\"chat_metadata_row_count\":" + std::to_string(jsonl_count(paths.chat_metadata)) + ","
        "\"unique_anchor_count\":" + std::to_string(anchor_counts.size()) + ","
        "\"anchor_observation_count\":" + std::to_string(postings.size()) + ","
        "\"relation_observation_count\":" + std::to_string(relation_total) + ","
        "\"count_backend\":\"" + std::string(COUNT_BACKEND) + "\","
        "\"compute_engine\":\"" + std::string(COMPUTE_ENGINE) + "\","
        "\"persistent_memory\":false,"
        "\"promotion_allowed\":false"
    );
    const auto receipt_path = paths.receipts / ("intake_" + now_stamp() + ".json");
    write_text(receipt_path, receipt.str() + "\n");
    std::string payload = receipt.str();
    payload.pop_back();
    payload += ",\"receipt_path\":\"" + json_escape(receipt_path.string()) + "\"}";
    std::cout << payload << "\n";
    return 0;
}

bool block_allowed(const Block& b, const std::string& after, const std::string& before, const std::string& speaker) {
    const auto date = b.chat.count("date") ? b.chat.at("date") : "";
    if (!speaker.empty()) {
        const auto sp = b.chat.count("speaker") ? b.chat.at("speaker") : "";
        if (sp != lower(speaker)) return false;
    }
    if (!after.empty() && !date.empty() && date < after.substr(0, 10)) return false;
    if (!before.empty() && !date.empty() && date > before.substr(0, 10)) return false;
    return true;
}

int cmd_query(int argc, char** argv) {
    const auto runtime = fs::path(arg_value(argc, argv, "--runtime-root"));
    const auto dataset = arg_value(argc, argv, "--dataset-id");
    const auto question = arg_value(argc, argv, "--question");
    const auto top_k = optional_int(argc, argv, "--top-k", 5);
    const auto after = optional_arg(argc, argv, "--created-after", "");
    const auto before = optional_arg(argc, argv, "--created-before", "");
    const auto speaker = optional_arg(argc, argv, "--speaker", "");
    ensure_dataset(runtime, dataset, "operator_defined");
    const auto paths = paths_for(runtime, dataset);
    const auto blocks = read_blocks(paths);
    const auto symbol_to_anchor = read_symbol_to_anchor(paths);
    const auto required = anchorize(question);
    const auto q = expand_query_anchors(required);
    const std::set<std::string> required_set(required.begin(), required.end());
    const std::set<std::string> qset(q.begin(), q.end());

    std::map<std::string, int> relation_score;
    const auto rel = read_binary(paths.relation_counts);
    for (std::size_t off = 0; off + RELATION_RECORD_SIZE <= rel.size(); off += RELATION_RECORD_SIZE) {
        Symbol6 a{}, b{};
        std::copy_n(rel.begin() + static_cast<std::ptrdiff_t>(off), 6, a.begin());
        std::copy_n(rel.begin() + static_cast<std::ptrdiff_t>(off + 6), 6, b.begin());
        const auto anchor = symbol_to_anchor.count(symbol_hex(a)) ? symbol_to_anchor.at(symbol_hex(a)) : "";
        const auto neighbor = symbol_to_anchor.count(symbol_hex(b)) ? symbol_to_anchor.at(symbol_hex(b)) : "";
        const auto count = static_cast<int>(read_u32_be(rel, off + 14));
        if (qset.count(anchor) && !qset.count(neighbor)) relation_score[neighbor] += count;
    }
    std::vector<std::pair<std::string, int>> neighbors(relation_score.begin(), relation_score.end());
    std::sort(neighbors.begin(), neighbors.end(), [](const auto& l, const auto& r) { return l.second > r.second; });
    if (neighbors.size() > 16) neighbors.resize(16);

    std::map<int, Candidate> candidates;
    std::map<std::string, int> posting_counts;
    const auto pst = read_binary(paths.block_anchor_postings);
    for (std::size_t off = 0; off + BLOCK_ANCHOR_RECORD_SIZE <= pst.size(); off += BLOCK_ANCHOR_RECORD_SIZE) {
        Symbol6 s{};
        std::copy_n(pst.begin() + static_cast<std::ptrdiff_t>(off), 6, s.begin());
        posting_counts[symbol_hex(s)] += 1;
    }
    for (std::size_t off = 0; off + BLOCK_ANCHOR_RECORD_SIZE <= pst.size(); off += BLOCK_ANCHOR_RECORD_SIZE) {
        Symbol6 s{};
        std::copy_n(pst.begin() + static_cast<std::ptrdiff_t>(off), 6, s.begin());
        const auto sym = symbol_hex(s);
        const auto anchor = symbol_to_anchor.count(sym) ? symbol_to_anchor.at(sym) : sym;
        double weight = 0.0;
        bool direct = false;
        if (qset.count(anchor)) {
            weight = 80.0;
            direct = true;
        } else {
            for (std::size_t i = 0; i < neighbors.size(); ++i) {
                if (neighbors[i].first == anchor) weight = std::max(weight, static_cast<double>(std::max<int>(1, 4 - static_cast<int>(i / 4))));
            }
        }
        if (weight <= 0.0) continue;
        const int block = static_cast<int>(read_u32_be(pst, off + 6));
        if (block < 0 || block >= static_cast<int>(blocks.size())) continue;
        if (!block_allowed(blocks[static_cast<std::size_t>(block)], after, before, speaker)) continue;
        auto& c = candidates[block];
        c.block = block;
        c.score += weight / std::sqrt(static_cast<double>(std::max(1, posting_counts[sym])));
        c.matched.insert(anchor);
        if (direct) {
            c.direct_hits += 1;
            c.direct_matched.insert(anchor);
        }
    }
    if (candidates.empty()) {
        for (const auto& b : blocks) {
            if (!block_allowed(b, after, before, speaker)) continue;
            const auto block_terms = anchorize(b.text);
            std::map<std::string, int> local_counts;
            for (const auto& anchor : block_terms) ++local_counts[anchor];
            double score = 0.0;
            Candidate c;
            c.block = b.ordinal;
            for (const auto& [anchor, observations] : local_counts) {
                double weight = 0.0;
                bool direct = false;
                if (qset.count(anchor)) {
                    weight = 80.0;
                    direct = true;
                } else {
                    for (std::size_t i = 0; i < neighbors.size(); ++i) {
                        if (neighbors[i].first == anchor) {
                            weight = std::max(weight, static_cast<double>(std::max<int>(1, 4 - static_cast<int>(i / 4))));
                        }
                    }
                }
                if (weight <= 0.0) continue;
                score += weight * static_cast<double>(observations);
                c.matched.insert(anchor);
                if (direct) {
                    c.direct_hits += observations;
                    c.direct_matched.insert(anchor);
                }
            }
            if (score > 0.0) {
                c.score = score;
                candidates[c.block] = c;
            }
        }
    }
    std::vector<Candidate> ranked;
    for (auto& [id, c] : candidates) {
        const auto anchors = anchorize(blocks[static_cast<std::size_t>(id)].text);
        c.anchor_count = static_cast<int>(std::max<std::size_t>(1, anchors.size()));
        c.density = c.score / std::sqrt(static_cast<double>(c.anchor_count));
        ranked.push_back(c);
    }
    std::sort(ranked.begin(), ranked.end(), [](const auto& l, const auto& r) {
        if (l.direct_hits != r.direct_hits) return l.direct_hits > r.direct_hits;
        if (l.density != r.density) return l.density > r.density;
        if (l.score != r.score) return l.score > r.score;
        return l.block < r.block;
    });
    std::vector<Block> accepted;
    std::vector<std::string> location_jsons;
    std::vector<std::string> rejected_jsons;
    std::vector<std::string> receipts;
    const bool unsupported = required_set.size() >= 4;
    for (const auto& c : ranked) {
        const auto& b = blocks[static_cast<std::size_t>(c.block)];
        const auto block_terms = anchorize(b.text);
        std::set<std::string> text_anchors(block_terms.begin(), block_terms.end());
        int covered = 0;
        for (const auto& term : required_set) if (text_anchors.count(term) || c.direct_matched.count(term)) ++covered;
        const double coverage = required_set.empty() ? 0.0 : static_cast<double>(covered) / static_cast<double>(required_set.size());
        const bool heading = trim(b.text).rfind("#", 0) == 0 && b.text.find('\n') == std::string::npos;
        std::vector<std::string> rejects;
        if (heading && coverage < 0.75) rejects.push_back("heading_without_content");
        if (unsupported && coverage < 0.50) rejects.push_back("unsupported_refusal_threshold");
        if (required_set.size() >= 3 && coverage < 0.34) rejects.push_back("predicate_object_coverage_miss");
        std::ostringstream qual;
        qual << "{\"schema\":\"awrag_candidate_qualification@1\",\"candidate\":\"" << b.marker
             << "\",\"qualified\":" << (rejects.empty() ? "true" : "false")
             << ",\"reject_reasons\":" << array_strings(rejects)
             << ",\"coverage\":" << std::fixed << std::setprecision(4) << coverage
             << ",\"heading_only\":" << (heading ? "true" : "false")
             << ",\"broad_heading\":false,\"path_or_config_candidate\":false,"
             << "\"qualified_score\":" << (c.density + 8.0 * coverage + std::min(4, c.direct_hits)) << "}";
        receipts.push_back(qual.str());
        const auto row = location_json(b, c.score, c.density, c.direct_hits, c.anchor_count, c.matched, c.direct_matched, qual.str());
        if (rejects.empty() && static_cast<int>(accepted.size()) < top_k) {
            accepted.push_back(b);
            location_jsons.push_back(row);
        } else if (static_cast<int>(rejected_jsons.size()) < top_k) {
            rejected_jsons.push_back(row);
        }
        if (static_cast<int>(location_jsons.size()) >= top_k && static_cast<int>(rejected_jsons.size()) >= top_k) break;
    }
    std::vector<std::string> neighbor_jsons;
    for (const auto& [anchor, score] : neighbors) {
        neighbor_jsons.push_back("{\"anchor\":\"" + json_escape(anchor) + "\",\"score\":" + std::to_string(score) + "}");
    }
    std::ostringstream packet;
    packet << "{\"instruction\":\"Use cited local evidence coordinates only. This packet is a facsimile output, not source evidence.\","
           << "\"citations_owned_by\":\"AWRAG\","
           << "\"qualification\":{\"schema\":\"awrag_evidence_qualification_summary@1\",\"support_state\":\""
           << (location_jsons.empty() ? "no_qualified_evidence" : "qualified_evidence")
           << "\",\"raw_candidate_count\":" << ranked.size()
           << ",\"qualified_count\":" << location_jsons.size()
           << ",\"rejected_count\":" << rejected_jsons.size()
           << ",\"required_terms\":" << array_strings(q) << ",\"path_or_config_intent\":false},"
           << "\"qualification_receipts\":["; 
    for (std::size_t i = 0; i < receipts.size(); ++i) { if (i) packet << ","; packet << receipts[i]; }
    packet << "],\"locations\":[";
    for (std::size_t i = 0; i < location_jsons.size(); ++i) { if (i) packet << ","; packet << location_jsons[i]; }
    packet << "],\"rejected_locations\":[";
    for (std::size_t i = 0; i < rejected_jsons.size(); ++i) { if (i) packet << ","; packet << rejected_jsons[i]; }
    packet << "]}";

    std::ostringstream out;
    out << protected_object(
        "\"schema\":\"awrag_query_result@1\","
        "\"created_at\":\"" + now_stamp() + "\","
        "\"dataset_id\":\"" + safe_id(dataset) + "\","
        "\"scope\":\"dataset_local\","
        "\"question\":\"" + json_escape(question) + "\","
        "\"question_anchors\":" + array_strings(q) + ","
        "\"relation_neighbors\":["
    );
    std::string prefix = out.str();
    prefix.pop_back();
    std::ostringstream full;
    full << prefix;
    for (std::size_t i = 0; i < neighbor_jsons.size(); ++i) { if (i) full << ","; full << neighbor_jsons[i]; }
    full << "],\"count_backend\":\"" << COUNT_BACKEND << "\",\"compute_engine\":\"" << COMPUTE_ENGINE
         << "\",\"model_used\":\"none\",\"model_may_search\":false,\"persistent_memory\":false,"
         << "\"metadata_filter\":{\"active\":" << ((!after.empty() || !before.empty() || !speaker.empty()) ? "true" : "false") << "},"
         << "\"answer_packet\":" << packet.str() << ","
         << "\"final_answer\":" << final_answer_json(accepted, q) << ","
         << "\"forensic_support_receipt\":" << forensic_json(accepted) << "}";
    const auto output_path = paths.outputs / ("query_" + now_stamp() + "_" + hex64(fnv1a64(question)).substr(0, 8) + ".json");
    write_text(output_path, full.str() + "\n");
    std::string payload = full.str();
    payload.pop_back();
    payload += ",\"output_path\":\"" + json_escape(output_path.string()) + "\"}";
    std::cout << payload << "\n";
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: awrag-counts <init|intake|status|query> ...\n";
        return 2;
    }
    try {
        const std::string command = argv[1];
        if (command == "init") return cmd_init(argc, argv);
        if (command == "intake") return cmd_intake(argc, argv);
        if (command == "status") return cmd_status(argc, argv);
        if (command == "query") return cmd_query(argc, argv);
        throw std::runtime_error("unknown command: " + command);
    } catch (const std::exception& exc) {
        std::cerr << "error: " << exc.what() << "\n";
        return 1;
    }
}
