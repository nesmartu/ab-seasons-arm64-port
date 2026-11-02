/* This file is part of the dynarmic project.
 * Copyright (c) 2022 MerryMage
 * SPDX-License-Identifier: 0BSD
 */

#pragma once

#include <mcl/stdint.hpp>

namespace oaknut {
struct CodeGenerator;
struct WReg;
}  // namespace oaknut

namespace Dynarmic::Backend::Arm64 {

class FpsrManager {
public:
    // absw: HostFpsr: with host_fpsr the host FPSR always holds the guest's flags (see Unsafe_HostFpsr):
    // Load and Spill emit nothing and GetFpsr merges the host FPSR into the state's value.
    explicit FpsrManager(oaknut::CodeGenerator& code, size_t state_fpsr_offset, bool host_fpsr = false);

    void Spill();
    void Load();
    void Overwrite() { fpsr_loaded = host_fpsr; }

    void GetFpsr(oaknut::WReg);

private:
    oaknut::CodeGenerator& code;
    size_t state_fpsr_offset;
    bool host_fpsr;
    bool fpsr_loaded;
};

}  // namespace Dynarmic::Backend::Arm64
