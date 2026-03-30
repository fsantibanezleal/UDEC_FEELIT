#include <filesystem>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace fs = std::filesystem;

struct BackendProfile {
  std::string slug;
  std::vector<std::string> marker_paths;
  std::vector<std::string> runtime_markers;
  std::string summary;
};

struct ProbeResult {
  std::string backend;
  std::string status = "scaffold-only";
  std::string summary = "Bridge scaffold compiled and responding, but no vendor SDK probe is linked yet.";
  std::string sdk_root;
  bool sdk_root_exists = false;
  std::vector<std::string> marker_hits;
  std::vector<std::string> runtime_hits;
  int device_count = 0;
  std::vector<std::string> devices;
  std::string runtime_library;
  std::string runtime_load_state = "not-applicable";
  std::string sdk_version;
};

static std::map<std::string, BackendProfile> build_profiles() {
  return {
      {"openhaptics-touch",
       {"openhaptics-touch",
        {"include/HD/hd.h", "include/HDU/hduVector.h"},
        {"lib/hd.lib", "lib/hdu.lib", "bin/hd.dll", "bin/hdu.dll"},
        "OpenHaptics-compatible Touch stack"}},
      {"forcedimension-dhd",
       {"forcedimension-dhd",
        {"include/dhdc.h", "include/drdc.h"},
        {"lib/dhd.lib", "lib/drd.lib", "bin/dhd64.dll", "bin/drd64.dll"},
        "Force Dimension DHD stack"}},
      {"chai3d-bridge",
       {"chai3d-bridge",
        {"src/devices/CGenericHapticDevice.h", "src/world/CWorld.h"},
        {"CMakeLists.txt", "src/devices/CGenericHapticDevice.h"},
        "CHAI3D-oriented compatibility bridge"}}};
}

static std::string json_escape(const std::string& value) {
  std::ostringstream output;
  for (char character : value) {
    switch (character) {
      case '\\':
        output << "\\\\";
        break;
      case '"':
        output << "\\\"";
        break;
      case '\n':
        output << "\\n";
        break;
      case '\r':
        output << "\\r";
        break;
      case '\t':
        output << "\\t";
        break;
      default:
        output << character;
        break;
    }
  }
  return output.str();
}

static std::string arg_value(int argc, char* argv[], const std::string& option, const std::string& fallback = "") {
  for (int index = 1; index < argc; ++index) {
    if (argv[index] == option && index + 1 < argc) {
      return argv[index + 1];
    }
  }
  return fallback;
}

static bool has_flag(int argc, char* argv[], const std::string& option) {
  for (int index = 1; index < argc; ++index) {
    if (argv[index] == option) {
      return true;
    }
  }
  return false;
}

static std::optional<fs::path> first_existing_candidate(const std::vector<fs::path>& candidates) {
  for (const auto& candidate : candidates) {
    if (fs::exists(candidate)) {
      return candidate;
    }
  }
  return std::nullopt;
}

static std::string platform_loader_error() {
#ifdef _WIN32
  DWORD error_code = GetLastError();
  if (error_code == 0) {
    return "Unknown loader error";
  }
  LPSTR message_buffer = nullptr;
  const DWORD size = FormatMessageA(
      FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
      nullptr,
      error_code,
      MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
      reinterpret_cast<LPSTR>(&message_buffer),
      0,
      nullptr);
  std::string message = size && message_buffer ? std::string(message_buffer, size) : "Unknown loader error";
  if (message_buffer) {
    LocalFree(message_buffer);
  }
  while (!message.empty() && (message.back() == '\n' || message.back() == '\r' || message.back() == ' ')) {
    message.pop_back();
  }
  return message;
#else
  const char* error = dlerror();
  return error ? std::string(error) : "Unknown loader error";
#endif
}

class SharedLibrary {
 public:
  SharedLibrary() = default;
  SharedLibrary(const SharedLibrary&) = delete;
  SharedLibrary& operator=(const SharedLibrary&) = delete;

  ~SharedLibrary() {
    close();
  }

  bool open(const fs::path& library_path, std::string* error) {
    close();
#ifdef _WIN32
    handle_ = LoadLibraryA(library_path.string().c_str());
#else
    handle_ = dlopen(library_path.string().c_str(), RTLD_NOW);
#endif
    if (!handle_) {
      if (error) {
        *error = platform_loader_error();
      }
      return false;
    }
    loaded_path_ = library_path.string();
    return true;
  }

  void close() {
    if (!handle_) {
      return;
    }
#ifdef _WIN32
    FreeLibrary(static_cast<HMODULE>(handle_));
#else
    dlclose(handle_);
#endif
    handle_ = nullptr;
    loaded_path_.clear();
  }

  template <typename FunctionType>
  FunctionType symbol(const char* symbol_name) const {
    if (!handle_) {
      return nullptr;
    }
#ifdef _WIN32
    auto raw = GetProcAddress(static_cast<HMODULE>(handle_), symbol_name);
#else
    auto raw = dlsym(handle_, symbol_name);
#endif
    return reinterpret_cast<FunctionType>(raw);
  }

  const std::string& loaded_path() const {
    return loaded_path_;
  }

 private:
#ifdef _WIN32
  HMODULE handle_ = nullptr;
#else
  void* handle_ = nullptr;
#endif
  std::string loaded_path_;
};

static ProbeResult build_default_probe_result(const std::string& backend_slug, const std::string& configured_sdk_root) {
  ProbeResult result;
  result.backend = backend_slug;
  result.sdk_root = configured_sdk_root;
  result.sdk_root_exists = !configured_sdk_root.empty() && fs::exists(fs::path(configured_sdk_root));
  return result;
}

static void apply_marker_hits(ProbeResult* result, const BackendProfile& profile) {
  if (!result->sdk_root_exists) {
    return;
  }

  const fs::path sdk_root(result->sdk_root);
  for (const auto& marker : profile.marker_paths) {
    if (fs::exists(sdk_root / marker)) {
      result->marker_hits.push_back(marker);
    }
  }
  for (const auto& marker : profile.runtime_markers) {
    if (fs::exists(sdk_root / marker)) {
      result->runtime_hits.push_back(marker);
    }
  }
}

static ProbeResult run_forcedimension_probe(const std::string& backend_slug, const std::string& configured_sdk_root, const BackendProfile& profile) {
  using dhdGetDeviceCountFn = int (*)();
  using dhdOpenFn = int (*)();
  using dhdOpenIDFn = int (*)(char);
  using dhdCloseFn = int (*)(char);
  using dhdErrorGetLastStrFn = const char* (*)();
  using dhdGetSystemNameFn = const char* (*)(char);
  using dhdGetSDKVersionStrFn = const char* (*)();

  ProbeResult result = build_default_probe_result(backend_slug, configured_sdk_root);
  result.runtime_load_state = "not-attempted";
  apply_marker_hits(&result, profile);

  if (!result.sdk_root_exists) {
    result.summary = "Bridge scaffold compiled, but the SDK root is missing or was not provided.";
    return result;
  }

  const fs::path sdk_root(result.sdk_root);
  const auto runtime_library = first_existing_candidate({
      sdk_root / "bin" / "dhd64.dll",
      sdk_root / "bin" / "dhd.dll",
      sdk_root / "lib" / "libdhd.so",
      sdk_root / "lib" / "libdhd.dylib",
  });

  if (!runtime_library) {
    result.status = "runtime-library-missing";
    result.runtime_load_state = "missing";
    result.summary = "Force Dimension SDK markers were found, but no supported DHD runtime library was present under the SDK root.";
    return result;
  }

  result.runtime_library = runtime_library->string();

  SharedLibrary library;
  std::string load_error;
  if (!library.open(*runtime_library, &load_error)) {
    result.status = "runtime-load-failed";
    result.runtime_load_state = "load-failed";
    result.summary = "Failed to load the Force Dimension runtime library: " + load_error;
    return result;
  }
  result.runtime_load_state = "loaded";

  auto dhd_get_device_count = library.symbol<dhdGetDeviceCountFn>("dhdGetDeviceCount");
  auto dhd_open = library.symbol<dhdOpenFn>("dhdOpen");
  auto dhd_open_id = library.symbol<dhdOpenIDFn>("dhdOpenID");
  auto dhd_close = library.symbol<dhdCloseFn>("dhdClose");
  auto dhd_error_get_last_str = library.symbol<dhdErrorGetLastStrFn>("dhdErrorGetLastStr");
  auto dhd_get_system_name = library.symbol<dhdGetSystemNameFn>("dhdGetSystemName");
  auto dhd_get_sdk_version_str = library.symbol<dhdGetSDKVersionStrFn>("dhdGetSDKVersionStr");

  if (!dhd_get_device_count || !dhd_open || !dhd_close || !dhd_error_get_last_str || !dhd_get_system_name || !dhd_get_sdk_version_str) {
    result.status = "runtime-symbol-missing";
    result.runtime_load_state = "symbols-missing";
    result.summary = "Force Dimension runtime loaded, but one or more required DHD symbols are missing.";
    return result;
  }

  const char* sdk_version = dhd_get_sdk_version_str();
  if (sdk_version) {
    result.sdk_version = sdk_version;
  }

  result.device_count = dhd_get_device_count();
  if (result.device_count <= 0) {
    const char* error = dhd_error_get_last_str();
    result.status = "runtime-loaded-no-devices";
    result.summary = "Force Dimension runtime loaded, but no devices were detected.";
    if (error && std::string(error).size() > 0) {
      result.summary += " ";
      result.summary += error;
    }
    return result;
  }

  if (dhd_open_id) {
    for (int index = 0; index < result.device_count; ++index) {
      const int device_id = dhd_open_id(static_cast<char>(index));
      if (device_id < 0) {
        const char* error = dhd_error_get_last_str();
        result.devices.push_back(
            std::string("Force Dimension device #") + std::to_string(index) +
            (error ? std::string(" (open failed: ") + error + ")" : " (open failed)"));
        continue;
      }
      const char* device_name = dhd_get_system_name(static_cast<char>(device_id));
      if (device_name && std::string(device_name).size() > 0) {
        result.devices.push_back(device_name);
      } else {
        result.devices.push_back(std::string("Force Dimension device #") + std::to_string(index));
      }
      dhd_close(static_cast<char>(device_id));
    }
  } else {
    const int device_id = dhd_open();
    if (device_id < 0) {
      const char* error = dhd_error_get_last_str();
      result.status = "device-open-failed";
      result.summary = "Force Dimension runtime detected devices, but the first device could not be opened.";
      if (error && std::string(error).size() > 0) {
        result.summary += " ";
        result.summary += error;
      }
      return result;
    }
    const char* device_name = dhd_get_system_name(static_cast<char>(device_id));
    if (device_name && std::string(device_name).size() > 0) {
      result.devices.push_back(device_name);
    } else {
      result.devices.push_back("Force Dimension device");
    }
    dhd_close(static_cast<char>(device_id));
  }

  result.status = "ready";
  result.summary = "Force Dimension runtime loaded and enumerated " + std::to_string(result.device_count) + " device(s).";
  return result;
}

static ProbeResult run_scaffold_probe(const std::string& backend_slug, const std::string& configured_sdk_root, const BackendProfile& profile) {
  ProbeResult result = build_default_probe_result(backend_slug, configured_sdk_root);
  apply_marker_hits(&result, profile);

  if (!result.sdk_root_exists) {
    result.summary = "Bridge scaffold compiled, but the SDK root is missing or was not provided.";
  } else if (result.marker_hits.empty()) {
    result.status = "sdk-root-present-but-markers-missing";
    result.summary = "SDK root exists, but the expected marker files were not found for this backend.";
  } else {
    result.summary = "SDK markers were found and the bridge scaffold can report probe JSON, but live device enumeration is not implemented yet.";
  }
  return result;
}

static void append_json_string(std::ostringstream* output, const std::string& key, const std::string& value, bool* first_field) {
  if (!*first_field) {
    *output << ",";
  }
  *first_field = false;
  *output << "\"" << key << "\":\"" << json_escape(value) << "\"";
}

static void append_json_bool(std::ostringstream* output, const std::string& key, bool value, bool* first_field) {
  if (!*first_field) {
    *output << ",";
  }
  *first_field = false;
  *output << "\"" << key << "\":" << (value ? "true" : "false");
}

static void append_json_int(std::ostringstream* output, const std::string& key, int value, bool* first_field) {
  if (!*first_field) {
    *output << ",";
  }
  *first_field = false;
  *output << "\"" << key << "\":" << value;
}

static void append_json_array(std::ostringstream* output, const std::string& key, const std::vector<std::string>& values, bool* first_field) {
  if (!*first_field) {
    *output << ",";
  }
  *first_field = false;
  *output << "\"" << key << "\":[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index > 0) {
      *output << ",";
    }
    *output << "\"" << json_escape(values[index]) << "\"";
  }
  *output << "]";
}

int main(int argc, char* argv[]) {
  const auto profiles = build_profiles();
  const std::string default_backend = FEELIT_BRIDGE_DEFAULT_BACKEND;
  const std::string backend_slug = arg_value(argc, argv, "--backend", default_backend.empty() ? "openhaptics-touch" : default_backend);
  const std::string configured_sdk_root = arg_value(argc, argv, "--sdk-root", FEELIT_VENDOR_SDK_ROOT);
  const bool emit_json = has_flag(argc, argv, "--emit-json");

  const auto profile_it = profiles.find(backend_slug);
  if (profile_it == profiles.end()) {
    std::cerr << "Unsupported backend slug: " << backend_slug << std::endl;
    return 2;
  }

  const BackendProfile& profile = profile_it->second;
  ProbeResult result =
      backend_slug == "forcedimension-dhd"
          ? run_forcedimension_probe(backend_slug, configured_sdk_root, profile)
          : run_scaffold_probe(backend_slug, configured_sdk_root, profile);

  if (!emit_json) {
    std::cout << result.summary << std::endl;
    return 0;
  }

  std::ostringstream output;
  bool first_field = true;
  output << "{";
  append_json_string(&output, "schema_version", "2", &first_field);
  append_json_string(&output, "backend", result.backend, &first_field);
  append_json_string(&output, "status", result.status, &first_field);
  append_json_string(&output, "summary", result.summary, &first_field);
  append_json_string(&output, "sdk_root", result.sdk_root, &first_field);
  append_json_bool(&output, "sdk_root_exists", result.sdk_root_exists, &first_field);
  append_json_array(&output, "marker_hits", result.marker_hits, &first_field);
  append_json_array(&output, "runtime_marker_hits", result.runtime_hits, &first_field);
  append_json_int(&output, "device_count", result.device_count, &first_field);
  append_json_array(&output, "devices", result.devices, &first_field);
  append_json_string(&output, "runtime_library", result.runtime_library, &first_field);
  append_json_string(&output, "runtime_load_state", result.runtime_load_state, &first_field);
  append_json_string(&output, "sdk_version", result.sdk_version, &first_field);
  output << "}";

  std::cout << output.str() << std::endl;
  return 0;
}
