#include <filesystem>
#include <iostream>
#include <map>
#include <cstdint>
#include <limits>
#include <optional>
#include <fstream>
#include <regex>
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
  std::vector<std::string> reported_capabilities;
  std::vector<std::string> probe_notes;
  std::vector<std::string> resolved_symbols;
  std::vector<std::string> open_attempt_labels;
  std::string enumeration_mode = "not-applicable";
  std::string device_identity_source = "not-applicable";
  std::string capability_scope = "none";
  std::string configured_device_selector;
  std::string effective_device_selector;
};

struct CommandAckResult {
  std::string backend;
  std::string status = "command-invalid";
  std::string summary = "The pilot command payload could not be validated.";
  std::string command_slug;
  std::string primitive_slug;
  std::string pilot_mode;
  std::string pilot_route;
  bool accepted = false;
  std::vector<std::string> validated_fields;
  std::vector<std::string> missing_fields;
  std::vector<std::string> notes;
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

static std::string read_text_file(const fs::path& file_path) {
  std::ifstream input(file_path, std::ios::binary);
  std::ostringstream buffer;
  buffer << input.rdbuf();
  return buffer.str();
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

static void append_unique(std::vector<std::string>* values, const std::string& value) {
  if (!values) {
    return;
  }
  for (const auto& existing : *values) {
    if (existing == value) {
      return;
    }
  }
  values->push_back(value);
}

static std::optional<std::string> extract_json_string_field(const std::string& payload, const std::string& key) {
  const std::regex pattern("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
  std::smatch match;
  if (std::regex_search(payload, match, pattern) && match.size() > 1) {
    return match[1].str();
  }
  return std::nullopt;
}

static bool contains_json_key(const std::string& payload, const std::string& key) {
  return payload.find("\"" + key + "\"") != std::string::npos;
}

static CommandAckResult run_pilot_command_ack(
    const std::string& backend_slug,
    const fs::path& command_file_path) {
  CommandAckResult result;
  result.backend = backend_slug;

  if (!fs::exists(command_file_path)) {
    result.summary = "The pilot command file is missing.";
    result.missing_fields.push_back("command_file");
    return result;
  }

  const std::string payload = read_text_file(command_file_path);
  const auto command_slug = extract_json_string_field(payload, "command_slug");
  const auto payload_backend_slug = extract_json_string_field(payload, "backend_slug");
  const auto primitive_slug = extract_json_string_field(payload, "primitive_slug");
  const auto pilot_mode = extract_json_string_field(payload, "pilot_mode");
  const auto pilot_route = extract_json_string_field(payload, "pilot_route");
  const auto schema_version = extract_json_string_field(payload, "schema_version");

  if (command_slug) {
    result.command_slug = *command_slug;
    result.validated_fields.push_back("command_slug");
  } else {
    result.missing_fields.push_back("command_slug");
  }
  if (payload_backend_slug) {
    result.validated_fields.push_back("backend_slug");
  } else {
    result.missing_fields.push_back("backend_slug");
  }
  if (primitive_slug) {
    result.primitive_slug = *primitive_slug;
    result.validated_fields.push_back("primitive_slug");
  } else {
    result.missing_fields.push_back("primitive_slug");
  }
  if (pilot_mode) {
    result.pilot_mode = *pilot_mode;
    result.validated_fields.push_back("pilot_mode");
  } else {
    result.missing_fields.push_back("pilot_mode");
  }
  if (pilot_route) {
    result.pilot_route = *pilot_route;
    result.validated_fields.push_back("pilot_route");
  } else {
    result.missing_fields.push_back("pilot_route");
  }
  if (schema_version) {
    result.validated_fields.push_back("schema_version");
  } else {
    result.missing_fields.push_back("schema_version");
  }

  if (contains_json_key(payload, "transport")) {
    result.validated_fields.push_back("transport");
  } else {
    result.missing_fields.push_back("transport");
  }
  if (contains_json_key(payload, "force_model")) {
    result.validated_fields.push_back("force_model");
  } else {
    result.missing_fields.push_back("force_model");
  }
  if (contains_json_key(payload, "safety_envelope")) {
    result.validated_fields.push_back("safety_envelope");
  } else {
    result.missing_fields.push_back("safety_envelope");
  }
  if (contains_json_key(payload, "telemetry_contract")) {
    result.validated_fields.push_back("telemetry_contract");
  } else {
    result.missing_fields.push_back("telemetry_contract");
  }

  if (!result.missing_fields.empty()) {
    result.summary = "The pilot command payload is missing one or more required contract fields.";
    return result;
  }

  if (!payload_backend_slug || *payload_backend_slug != backend_slug) {
    result.status = "command-backend-mismatch";
    result.summary = "The pilot command backend does not match the native bridge backend target.";
    result.notes.push_back("A bridge-side consumer must reject commands addressed to another backend family.");
    return result;
  }

  result.status = "command-acknowledged-dry-run";
  result.accepted = true;
  result.summary =
      "The native bridge accepted the dry-run pilot command contract for validation only. "
      "No servo loop, force output, or scene ownership was started.";
  result.notes.push_back(
      "This acknowledgement only proves that the native boundary can receive and validate one bounded pilot payload.");
  result.notes.push_back(
      "Real actuation, bridge-side execution, and force-loop ownership remain future work.");
  return result;
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

  if (dhd_get_device_count) {
    result.resolved_symbols.push_back("dhdGetDeviceCount");
  }
  if (dhd_open) {
    result.resolved_symbols.push_back("dhdOpen");
  }
  if (dhd_open_id) {
    result.resolved_symbols.push_back("dhdOpenID");
  }
  if (dhd_close) {
    result.resolved_symbols.push_back("dhdClose");
  }
  if (dhd_error_get_last_str) {
    result.resolved_symbols.push_back("dhdErrorGetLastStr");
  }
  if (dhd_get_system_name) {
    result.resolved_symbols.push_back("dhdGetSystemName");
  }
  if (dhd_get_sdk_version_str) {
    result.resolved_symbols.push_back("dhdGetSDKVersionStr");
  }

  if (!dhd_get_device_count || !dhd_open || !dhd_close || !dhd_error_get_last_str || !dhd_get_system_name || !dhd_get_sdk_version_str) {
    result.status = "runtime-symbol-missing";
    result.runtime_load_state = "symbols-missing";
    result.summary = "Force Dimension runtime loaded, but one or more required DHD symbols are missing.";
    return result;
  }

  result.enumeration_mode = dhd_open_id ? "per-device-open-id" : "first-device-open";
  result.device_identity_source = "sdk-system-name";
  result.capability_scope = "runtime-and-live-device-enumeration";
  result.reported_capabilities = {
      "device-detection",
      "workspace-alignment",
      "force-feedback-path",
      "servo-loop-telemetry",
  };
  result.probe_notes.push_back(
      "The DHD probe reports a real runtime-backed enumeration path. It still does not claim that scene-coupled force rendering is wired into FeelIT yet.");

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

static bool probe_handle_is_valid(void* handle) {
  if (!handle) {
    return false;
  }
  const auto value = reinterpret_cast<std::uintptr_t>(handle);
  return value != (std::numeric_limits<std::uintptr_t>::max)();
}

static ProbeResult run_openhaptics_probe(
    const std::string& backend_slug,
    const std::string& configured_sdk_root,
    const std::string& configured_device_selector,
    const BackendProfile& profile) {
  using hdInitDeviceFn = void* (*)(const char*);
  using hdDisableDeviceFn = void (*)(void*);
  using hdGetErrorStringFn = const char* (*)(int);
  using hdGetStringFn = const char* (*)(int);
  using hdGetCurrentDeviceFn = void* (*)();
  using hdGetIntegervFn = void (*)(int, int*);
  using hdGetDoublevFn = void (*)(int, double*);
  using hdEnableFn = void (*)(int);
  using hdSetDoublevFn = void (*)(int, const double*);
  using hdStartSchedulerFn = int (*)();
  using hdStopSchedulerFn = int (*)();
  using hdScheduleAsynchronousFn = void* (*)(void*, void*, int);
  using hdUnscheduleFn = int (*)(void*);
  using hdCheckCalibrationFn = int (*)();
  using hdUpdateCalibrationFn = int (*)(int);

  ProbeResult result = build_default_probe_result(backend_slug, configured_sdk_root);
  result.configured_device_selector = configured_device_selector;
  result.runtime_load_state = "not-attempted";
  apply_marker_hits(&result, profile);

  if (!result.sdk_root_exists) {
    result.summary = "Bridge scaffold compiled, but the SDK root is missing or was not provided.";
    return result;
  }

  const fs::path sdk_root(result.sdk_root);
  const auto runtime_library = first_existing_candidate({
      sdk_root / "bin" / "hd.dll",
      sdk_root / "lib" / "hd.dll",
  });
  const auto utility_library = first_existing_candidate({
      sdk_root / "bin" / "hdu.dll",
      sdk_root / "lib" / "hdu.dll",
  });

  if (!runtime_library) {
    result.status = "runtime-library-missing";
    result.runtime_load_state = "missing";
    result.summary = "OpenHaptics SDK markers were found, but no supported HD runtime library was present under the SDK root.";
    return result;
  }

  result.runtime_library = runtime_library->string();

  SharedLibrary hd_library;
  std::string load_error;
  if (!hd_library.open(*runtime_library, &load_error)) {
    result.status = "runtime-load-failed";
    result.runtime_load_state = "load-failed";
    result.summary = "Failed to load the OpenHaptics HD runtime library: " + load_error;
    return result;
  }
  result.runtime_load_state = "loaded";

  SharedLibrary hdu_library;
  if (utility_library) {
    std::string utility_error;
    if (!hdu_library.open(*utility_library, &utility_error)) {
      result.status = "runtime-load-failed";
      result.runtime_load_state = "utility-load-failed";
      result.summary = "OpenHaptics HD runtime loaded, but the HDU utility library failed to load: " + utility_error;
      return result;
    }
  }

  auto hd_init_device = hd_library.symbol<hdInitDeviceFn>("hdInitDevice");
  auto hd_disable_device = hd_library.symbol<hdDisableDeviceFn>("hdDisableDevice");
  auto hd_get_error_string = hd_library.symbol<hdGetErrorStringFn>("hdGetErrorString");
  auto hd_get_string = hd_library.symbol<hdGetStringFn>("hdGetString");
  auto hd_get_current_device = hd_library.symbol<hdGetCurrentDeviceFn>("hdGetCurrentDevice");
  auto hd_get_integerv = hd_library.symbol<hdGetIntegervFn>("hdGetIntegerv");
  auto hd_get_doublev = hd_library.symbol<hdGetDoublevFn>("hdGetDoublev");
  auto hd_enable = hd_library.symbol<hdEnableFn>("hdEnable");
  auto hd_set_doublev = hd_library.symbol<hdSetDoublevFn>("hdSetDoublev");
  auto hd_start_scheduler = hd_library.symbol<hdStartSchedulerFn>("hdStartScheduler");
  auto hd_stop_scheduler = hd_library.symbol<hdStopSchedulerFn>("hdStopScheduler");
  auto hd_schedule_async = hd_library.symbol<hdScheduleAsynchronousFn>("hdScheduleAsynchronous");
  auto hd_unschedule = hd_library.symbol<hdUnscheduleFn>("hdUnschedule");
  auto hd_check_calibration = hd_library.symbol<hdCheckCalibrationFn>("hdCheckCalibration");
  auto hd_update_calibration = hd_library.symbol<hdUpdateCalibrationFn>("hdUpdateCalibration");

  if (hd_init_device) {
    result.resolved_symbols.push_back("hdInitDevice");
  }
  if (hd_disable_device) {
    result.resolved_symbols.push_back("hdDisableDevice");
  }
  if (hd_get_error_string) {
    result.resolved_symbols.push_back("hdGetErrorString");
  }
  if (hd_get_string) {
    result.resolved_symbols.push_back("hdGetString");
  }
  if (hd_get_current_device) {
    result.resolved_symbols.push_back("hdGetCurrentDevice");
  }
  if (hd_get_integerv) {
    result.resolved_symbols.push_back("hdGetIntegerv");
  }
  if (hd_get_doublev) {
    result.resolved_symbols.push_back("hdGetDoublev");
  }
  if (hd_enable) {
    result.resolved_symbols.push_back("hdEnable");
  }
  if (hd_set_doublev) {
    result.resolved_symbols.push_back("hdSetDoublev");
  }
  if (hd_start_scheduler) {
    result.resolved_symbols.push_back("hdStartScheduler");
  }
  if (hd_stop_scheduler) {
    result.resolved_symbols.push_back("hdStopScheduler");
  }
  if (hd_schedule_async) {
    result.resolved_symbols.push_back("hdScheduleAsynchronous");
  }
  if (hd_unschedule) {
    result.resolved_symbols.push_back("hdUnschedule");
  }
  if (hd_check_calibration) {
    result.resolved_symbols.push_back("hdCheckCalibration");
  }
  if (hd_update_calibration) {
    result.resolved_symbols.push_back("hdUpdateCalibration");
  }

  if (!hd_init_device || !hd_disable_device || !hd_get_error_string) {
    result.status = "runtime-symbol-missing";
    result.runtime_load_state = "symbols-missing";
    result.summary = "OpenHaptics runtime loaded, but one or more minimal HDAPI entry points are missing.";
    return result;
  }

  result.enumeration_mode = "default-device-open";
  result.capability_scope = "runtime-and-default-device-open";
  append_unique(&result.reported_capabilities, "device-open-close");
  append_unique(&result.reported_capabilities, "error-reporting");
  append_unique(&result.reported_capabilities, "force-enable-disable");
  if (hd_get_current_device) {
    append_unique(&result.reported_capabilities, "device-context-query");
  }
  if (hd_get_string || hd_get_integerv || hd_get_doublev) {
    append_unique(&result.reported_capabilities, "device-characteristics-query");
    append_unique(&result.reported_capabilities, "device-state-query");
  }
  if (hd_get_integerv) {
    append_unique(&result.reported_capabilities, "button-proxy-input-path");
  }
  if (hd_set_doublev) {
    append_unique(&result.reported_capabilities, "force-output-path");
  }
  if (hd_start_scheduler || hd_stop_scheduler || hd_schedule_async || hd_unschedule) {
    append_unique(&result.reported_capabilities, "scheduler-control");
  }
  if (hd_check_calibration || hd_update_calibration) {
    append_unique(&result.reported_capabilities, "calibration-interface");
  }
  result.probe_notes.push_back(
      "OpenHaptics capability reporting is currently based on exported HDAPI symbol availability plus a conservative default-device open attempt. It does not yet claim live scene-coupled force output.");

  std::vector<const char*> device_selectors;
  if (!result.configured_device_selector.empty()) {
    device_selectors.push_back(result.configured_device_selector.c_str());
  }
  device_selectors.push_back("DEFAULT");
  device_selectors.push_back("Default PHANToM");
  void* device_handle = nullptr;
  std::string selector_used;
  for (const auto* selector : device_selectors) {
    result.open_attempt_labels.push_back(selector);
    device_handle = hd_init_device(selector);
    if (probe_handle_is_valid(device_handle)) {
      selector_used = selector;
      break;
    }
  }

  if (probe_handle_is_valid(device_handle)) {
    result.status = "ready";
    result.device_count = 1;
    result.device_identity_source = "fallback-default-open-label";
    result.effective_device_selector = selector_used;
    result.devices.push_back(
        selector_used.empty() ? "OpenHaptics default device" : "OpenHaptics default device (" + selector_used + ")");
    result.summary =
        "OpenHaptics runtime libraries loaded and a default-device open probe succeeded for safe enumeration.";
    hd_disable_device(device_handle);
    return result;
  }

  result.status = "runtime-loaded-capability-ready";
  result.device_identity_source = "not-reported";
  result.summary =
      "OpenHaptics runtime libraries loaded and HDAPI entry points are available, but the conservative default-device open probe did not yield a usable handle.";
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

static void append_json_ack_result(std::ostringstream* output, const CommandAckResult& result) {
  bool first_field = true;
  *output << "{";
  append_json_string(output, "schema_version", "1", &first_field);
  append_json_string(output, "mode", "pilot-command-ack", &first_field);
  append_json_string(output, "backend", result.backend, &first_field);
  append_json_string(output, "status", result.status, &first_field);
  append_json_string(output, "summary", result.summary, &first_field);
  append_json_string(output, "command_slug", result.command_slug, &first_field);
  append_json_string(output, "primitive_slug", result.primitive_slug, &first_field);
  append_json_string(output, "pilot_mode", result.pilot_mode, &first_field);
  append_json_string(output, "pilot_route", result.pilot_route, &first_field);
  append_json_bool(output, "accepted", result.accepted, &first_field);
  append_json_array(output, "validated_fields", result.validated_fields, &first_field);
  append_json_array(output, "missing_fields", result.missing_fields, &first_field);
  append_json_array(output, "notes", result.notes, &first_field);
  *output << "}";
}

int main(int argc, char* argv[]) {
  const auto profiles = build_profiles();
  const std::string default_backend = FEELIT_BRIDGE_DEFAULT_BACKEND;
  const std::string backend_slug = arg_value(argc, argv, "--backend", default_backend.empty() ? "openhaptics-touch" : default_backend);
  const std::string configured_sdk_root = arg_value(argc, argv, "--sdk-root", FEELIT_VENDOR_SDK_ROOT);
  const std::string configured_device_selector = arg_value(argc, argv, "--device-selector");
  const std::string command_file = arg_value(argc, argv, "--consume-pilot-command-file");
  const bool emit_json = has_flag(argc, argv, "--emit-json");

  const auto profile_it = profiles.find(backend_slug);
  if (profile_it == profiles.end()) {
    std::cerr << "Unsupported backend slug: " << backend_slug << std::endl;
    return 2;
  }

  const BackendProfile& profile = profile_it->second;
  if (!command_file.empty()) {
    const CommandAckResult command_ack = run_pilot_command_ack(backend_slug, fs::path(command_file));
    if (!emit_json) {
      std::cout << command_ack.summary << std::endl;
      return command_ack.accepted ? 0 : 3;
    }
    std::ostringstream output;
    append_json_ack_result(&output, command_ack);
    std::cout << output.str() << std::endl;
    return command_ack.accepted ? 0 : 3;
  }

  ProbeResult result =
      backend_slug == "forcedimension-dhd"
          ? run_forcedimension_probe(backend_slug, configured_sdk_root, profile)
          : backend_slug == "openhaptics-touch"
                ? run_openhaptics_probe(
                      backend_slug,
                      configured_sdk_root,
                      configured_device_selector,
                      profile)
          : run_scaffold_probe(backend_slug, configured_sdk_root, profile);
  if (backend_slug != "openhaptics-touch") {
    result.configured_device_selector = configured_device_selector;
  }

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
  append_json_array(&output, "reported_capabilities", result.reported_capabilities, &first_field);
  append_json_array(&output, "probe_notes", result.probe_notes, &first_field);
  append_json_array(&output, "resolved_symbols", result.resolved_symbols, &first_field);
  append_json_array(&output, "open_attempt_labels", result.open_attempt_labels, &first_field);
  append_json_string(&output, "enumeration_mode", result.enumeration_mode, &first_field);
  append_json_string(&output, "device_identity_source", result.device_identity_source, &first_field);
  append_json_string(&output, "capability_scope", result.capability_scope, &first_field);
  append_json_string(&output, "configured_device_selector", result.configured_device_selector, &first_field);
  append_json_string(&output, "effective_device_selector", result.effective_device_selector, &first_field);
  output << "}";

  std::cout << output.str() << std::endl;
  return 0;
}
