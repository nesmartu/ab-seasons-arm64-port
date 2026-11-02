// Entry point: the arm64/x86_64 libAngryBirdsSeasonsFull.so that hosts the original ARM32 engine.
#include <jni.h>

#include <cstdint>

// The original, unmodified ARM32 image is read-only data inside the ELF64 bridge.
// It never passes through Android's native linker.
extern "C" const uint8_t abs662_guest_image[];
extern "C" const uint8_t abs662_guest_image_end[];

#include "arena.h"
#include "common.h"
#include "cpu.h"
#include "elf32.h"
#include "hle.h"
#include "jni_bridge.h"
#include "perf.h"

namespace {

const uint8_t kGuestRt[] = {
#include "guest_rt_blob.inc"
};

}  // namespace

extern "C" JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void*) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) return JNI_ERR;
#if defined(__aarch64__)
    LOGI("Seasons 6.6.2 ARM32 bridge starting (host arm64)");
#else
    LOGI("Seasons 6.6.2 ARM32 bridge starting (host x86_64)");
#endif
    perf::init();
    perf::mark("bridge JNI_OnLoad");
    arena::init();
    cpu::init();
    hle::init();
    jni::init(vm, env);

    elf::Module* rt = elf::load("libabsw_rt.so", kGuestRt, sizeof kGuestRt);
    elf::run_init(rt);

    const size_t image_size = static_cast<size_t>(abs662_guest_image_end - abs662_guest_image);
    LOGI("embedded original Seasons engine: %zu bytes", image_size);
    elf::Module* game = elf::load("libAngryBirdsSeasonsFull.so", abs662_guest_image, image_size);
    elf::run_init(game);
    perf::mark("guest constructors done");

    int bound = jni::bind_exports(env);
    LOGI("bound %d native methods", bound);

    jint version = JNI_VERSION_1_6;
    if (auto it = game->exports.find("JNI_OnLoad"); it != game->exports.end()) {
        jni::Scope scope(env);
        version = static_cast<jint>(cpu::call(it->second, {jni::guest_vm(), 0}));
        LOGI("guest JNI_OnLoad returned 0x%x", version);
    }
    perf::mark("bridge JNI_OnLoad done");
    return version;
}
