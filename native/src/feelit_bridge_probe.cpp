#include <filesystem>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

struct BackendProfile {
  std::string slug;
  std::vector<std::string> marker_paths;
  std::vector<std::string> runtime_markers;
  std::string summary;
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
  fs::path sdk_root(configured_sdk_root);
  const bool sdk_root_exists = !configured_sdk_root.empty() && fs::exists(sdk_root);

  std::vector<std::string> marker_hits;
  std::vector<std::string> runtime_hits;

  if (sdk_root_exists) {
    for (const auto& marker : profile.marker_paths) {
      if (fs::exists(sdk_root / marker)) {
        marker_hits.push_back(marker);
      }
    }
    for (const auto& marker : profile.runtime_markers) {
      if (fs::exists(sdk_root / marker)) {
        runtime_hits.push_back(marker);
      }
    }
  }

  std::string status = "scaffold-only";
  std::string summary = "Bridge scaffold compiled and responding, but no vendor SDK probe is linked yet.";
  if (!sdk_root_exists) {
    status = "scaffold-only";
    summary = "Bridge scaffold compiled, but the SDK root is missing or was not provided.";
  } else if (marker_hits.empty()) {
    status = "sdk-root-present-but-markers-missing";
    summary = "SDK root exists, but the expected marker files were not found for this backend.";
  } else {
    status = "scaffold-only";
    summary = "SDK markers were found and the bridge scaffold can report probe JSON, but live device enumeration is not implemented yet.";
  }

  if (!emit_json) {
    std::cout << summary << std::endl;
    return 0;
  }

  std::ostringstream output;
  output << "{";
  output << "\"schema_version\":\"1\",";
  output << "\"backend\":\"" << json_escape(backend_slug) << "\",";
  output << "\"status\":\"" << json_escape(status) << "\",";
  output << "\"summary\":\"" << json_escape(summary) << "\",";
  output << "\"sdk_root\":\"" << json_escape(configured_sdk_root) << "\",";
  output << "\"sdk_root_exists\":" << (sdk_root_exists ? "true" : "false") << ",";
  output << "\"marker_hits\":[";
  for (std::size_t index = 0; index < marker_hits.size(); ++index) {
    if (index > 0) {
      output << ",";
    }
    output << "\"" << json_escape(marker_hits[index]) << "\"";
  }
  output << "],";
  output << "\"runtime_marker_hits\":[";
  for (std::size_t index = 0; index < runtime_hits.size(); ++index) {
    if (index > 0) {
      output << ",";
    }
    output << "\"" << json_escape(runtime_hits[index]) << "\"";
  }
  output << "],";
  output << "\"device_count\":0,";
  output << "\"devices\":[]";
  output << "}";

  std::cout << output.str() << std::endl;
  return 0;
}
