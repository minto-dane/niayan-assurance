# Distro foundation: requirement / implementation / test / boundary

|Requirement|Source|Ada test prepared|Not established here|
|---|---|---|---|
|Bounded proc/sys reads independent of st_size|MC_Kernel_Read,MC_Clock|run_host_io_tests|Ada execution; compromised kernel/namespace attestation|
|Unknown host facts cannot authorize new effects|State_Host_Admission|run_platform_tests.Hosts|site aggregation/signature/freshness enforcement|
|Dependency/ordering/conflict separation and budgets|State_Service_Catalogue|run_platform_tests.Catalogue|unit activation/effective drop-ins/actual enforcement|
|Durable checkpoint before network mutation|State_Network_Controller|compile-all; generic callback contract|live anchor, NetworkManager, crash/disconnect tests|
|No blind resend, positive dwell, negative evidence resets|State_Network_Change|run_platform_tests.Network|real observation authentication and complete rollback coverage|
|Unique-owner fixed-method D-Bus checkpoint calls|State_NM_Checkpoint|compile-all; source review|real D-Bus owner credential verification/per-device restoration|
|Only exact stable boot candidate is eligible|State_Boot_Assessment|run_platform_tests.Boot|signed image installation, TPM/UEFI/BLS integration|
|Exact kernel/initramfs/driver composition|Pkg_System_Composition|run_composition_tests|full RPM inventory/native ownership migration|
|Signed subject-bound independent approvals|MC_Qualification,MC_Qualification_Auth|run_qualification_tests|actual proof/test artifacts and trustworthy report issuers|
|Independent RPM deployment without auto activation|packaging/rpm/*.spec|source harness; future rpmbuild|rpmbuild/install/erase, vendor support, reproducibility|
|Independent repos retain exact shared code|ci/check-contract.sh,Contract_Lock|source negative checks,cross-repository.sh|release authenticity itself|

Reference harnesses are separate implementations/checks, not execution or proof of these Ada units.
The supplied source is NOT a bootable distro image or production qualification.
