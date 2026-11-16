// Geometry-only OBJ parsing for Blender navigation imports. Rendering imports
// use Python.
#include <charconv>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <exception>
#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <vector>
struct Geometry {
  std::vector<float> vertices;
  std::vector<std::uint32_t> triangles;
};
struct Result {
  std::uint64_t vertices, triangles;
  const float *positions;
  const std::uint32_t *indices;
  void *owner;
};
static bool space(char c) { return c == ' ' || c == '\t' || c == '\r'; }
extern "C" __declspec(dllexport) void wowobj_free(Result *result) {
  if (result) {
    delete static_cast<Geometry *>(result->owner);
    *result = {};
  }
}
extern "C" __declspec(dllexport) int wowobj_load(const wchar_t *path,
                                                 Result *result, char *error,
                                                 std::uint64_t capacity) {
  if (!path || !result || !error || capacity < 1)
    return 0;
  *result = {};
  error[0] = 0;
  auto fail = [&](const std::string &message) {
    std::snprintf(error, static_cast<std::size_t>(capacity), "%s",
                  message.c_str());
    return 0;
  };
  try {
    std::ifstream file(std::filesystem::path(path),
                       std::ios::binary | std::ios::ate);
    if (!file)
      return fail("Cannot open OBJ");
    const auto length = file.tellg();
    if (length < 0 || length > 1024ll * 1024 * 1024)
      return fail("OBJ exceeds 1 GiB geometry parser limit");
    std::string source(static_cast<std::size_t>(length), '\0');
    file.seekg(0);
    if (!file.read(source.data(), length))
      return fail("Cannot read OBJ");
    auto geometry = std::make_unique<Geometry>();
    std::vector<std::uint32_t> face;
    face.reserve(8);
    const char *cursor = source.data();
    const char *end = cursor + source.size();
    std::size_t line = 0;
    while (cursor < end) {
      ++line;
      const auto *newline = static_cast<const char *>(
          std::memchr(cursor, '\n', static_cast<std::size_t>(end - cursor)));
      const char *stop = newline ? newline : end;
      const char *p = cursor;
      cursor = newline ? newline + 1 : end;
      while (p < stop && space(*p))
        ++p;
      if (stop - p < 2 || !space(p[1]))
        continue;
      if (*p == 'v') {
        ++p;
        for (int component = 0; component < 3; ++component) {
          while (p < stop && space(*p))
            ++p;
          if (p < stop && *p == '+')
            ++p;
          float value{};
          auto parsed = std::from_chars(p, stop, value);
          if (parsed.ec != std::errc{} || !std::isfinite(value) ||
              std::fabs(value) > 1000000 || (parsed.ptr != stop && !space(*parsed.ptr)))
            return fail("Invalid vertex on line " + std::to_string(line));
          geometry->vertices.push_back(value);
          p = parsed.ptr;
        }
      } else if (*p == 'f') {
        ++p;
        face.clear();
        while (p < stop) {
          while (p < stop && space(*p))
            ++p;
          if (p == stop || *p == '#')
            break;
          const char *token = p;
          while (p < stop && !space(*p))
            ++p;
          const char *start = token;
          if (*start == '+')
            ++start;
          std::int64_t index{};
          auto parsed = std::from_chars(start, p, index);
          const auto count =
              static_cast<std::int64_t>(geometry->vertices.size() / 3);
          if (parsed.ec != std::errc{} || !index ||
              (parsed.ptr != p && *parsed.ptr != '/'))
            return fail("Invalid face on line " + std::to_string(line));
          index = index > 0 ? index - 1 : count + index;
          if (index < 0 || index >= count || index > 0x7fffffff)
            return fail("Vertex index out of range on line " +
                        std::to_string(line));
          face.push_back(static_cast<std::uint32_t>(index));
          if (face.size() > 65536)
            return fail("OBJ face has too many corners");
        }
        for (std::size_t i = 2; i < face.size(); ++i) {
          geometry->triangles.push_back(face[0]);
          geometry->triangles.push_back(face[i - 1]);
          geometry->triangles.push_back(face[i]);
        }
      }
    }
    result->vertices = geometry->vertices.size() / 3;
    result->triangles = geometry->triangles.size() / 3;
    result->positions = geometry->vertices.data();
    result->indices = geometry->triangles.data();
    result->owner = geometry.release();
    return 1;
  } catch (const std::exception &ex) {
    return fail(ex.what());
  }
}
