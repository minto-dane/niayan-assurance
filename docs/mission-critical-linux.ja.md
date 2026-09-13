> 過去の別系統版から統合した参考文書です。記載された実装モデルの復元を意味し、収集器・実機接続・形式証明の完成を意味しません。現在の統合範囲は `assurance/docs/engineering/specs/unified-management.ja.md` と機能台帳を参照してください。

# Mission Core: ミッションクリティカル Linux 参照アーキテクチャ

## 目的

Mission Core は Linux カーネル、systemd、SELinux、既存ファイルシステム、既存 HA/DB を置き換えるディストリビューションではない。
それらの成熟部品の上で、**変更、実行状態、故障、復旧、承認、監査を一つの明示状態モデルに接続する**ための管理コアである。

最上位の不変条件は次のとおり。

1. 不明な状態を正常状態として公開しない。
2. 書き込み所有権は常に一つの管理主体だけが持つ。
3. 旧 writer の隔離を確認する前に新 writer を昇格しない。
4. APPLY と ACCEPT と COMMIT を分離する。
5. パッケージ復旧と業務データ復旧を混同しない。
6. 信頼・失効・監査の単調情報はソフトウェア rollback と一緒に巻き戻さない。
7. 自動復旧は試行予算、依存関係、証拠、安定観測を満たす場合だけ行う。
8. emergency/break-glass でも verification、audit、encryption を解除しない。
9. 物理 fencing、外部 DB、ストレージ、TPM 等の外部事実は qualified adapter の証拠として扱い、boolean 自己申告を信頼しない。
10. 形式検証の範囲外は TCB/assumption として公開する。

## 3コードベース

### assurance

信頼境界、暗号署名、認可、変更停止、証拠形式、障害報告、incident、platform admission、commissioning、system baseline、generation、audit/accounting を担当する。

新しい主要単位:

- `MC_Faults`, `MC_Fault_Report`, `MC_Incidents`: FMA 型の fault/incident 管理。
- `MC_Platform_Profile`: production admission checklist。
- `MC_Commissioning`: trust/storage/recovery/baseline を順序付きで commission。
- `MC_System_Baseline`: package set、kernel、boot、SELinux、integrity、recovery を一つの受入 baseline に束縛。
- `MC_Generation`: proposed → staged → canary → verified → accepted → committed。
- `MC_Accounting`: 変更・隔離・復旧・break-glass を hash-chain/remote receipt に載せる意味モデル。
- `MC_Breakglass`: containment/recovery の緊急認可。security boundary の解除操作は型として拒否。
- `MC_Diagnostic_Bundle`: kernel/RAS/audit/package journal 等を incident に束縛。

### pkgcore

RPM を入力形式とし、外部ディストリビューションの既存 binary repository を利用しつつ、Mission Core が理解・検証できる操作だけを変更エンジンへ渡す。

- RPM admission/provenance/file plan/CAS/WAL/recovery。
- `Pkg_Holds`: SMP/E HOLDDATA に相当する既知障害・運用 hold。
- `Pkg_Acceptance`: installp 型 APPLY/VERIFY/ACCEPT/COMMIT/REJECT。
- `Pkg_Incorporation`: Solaris IPS incorporation 型の exact tested composition。
- `Pkg_Repository_Trust`: repository epoch/snapshot/timestamp の rollback/freeze 防止用 anchor。
- `Pkg_Exposure_Policy`: 信頼機関の実環境悪用確認報告/critical fix の最大露出時間を policy 化。
- `Pkg_Rollback_Contract`: config/data migration の reversible/restore semantics。
- `Pkg_Maintenance_Bundle`: cumulative maintenance set / group maintenance level。

任意 RPM scriptlet を root で実行することを「検証済み互換性」と呼ばない。対応 contract のない effect は strict mode では拒否する。

### statecore

running state、service semantics、HA、RAS、resource safety、自動復旧を担当する。

- systemd/Pacemaker/etcd adapters と single-owner authority model。
- service health/recovery/rollout/readmission/disaster。
- quorum/fencing/fault-domain/capacity budgets。
- `State_RAS`, `State_FRU_Health`, `State_Storage_Integrity`, `State_Network_Integrity`, `State_Power_Integrity`。
- `State_Time_Integrity`: wall clock と monotonic lease を区別。
- `State_WLM`: service class / SLO / pressure による workload decision。
- `State_Kernel_Maintenance`: livepatch と rolling reboot の安全判定。
- `State_Self_Test`: restore/failover/fence/watchdog 等の定期 rehearsal を production budget 内で実施するための gate。
- `State_Serviceability`: out-of-band recovery、dump、audit、restore を含む serviceability grade。
- `State_Platform_Health`: subsystem の失敗を availability より integrity 優先で集約。

## 管理モデルとして採用する概念

| 概念 | Mission Core |
|---|---|
| 適用・検証・受入・確定の分離と保留条件 | holds, package acceptance, generation |
| workload goal と重要度 | `State_WLM` |
| 変更・障害の会計と監査 | `MC_Accounting` |
| quorum、fencing、rolling maintenance | cluster safety / rollout / authority |
| APPLY→COMMIT/REJECT | `Pkg_Acceptance` |
| hardware fault と serviceability | RAS/FRU/serviceability |
| exact image constraint | incorporation/system baseline |
| fault correlation、diagnosis、repair lifecycle | fault/incident/correlation |
| service contract と recovery | `State_Service` + systemd adapter |
| 起動可能な既知正常世代 | generation/checkpoint/boot acceptance; actual FS adapter external |

## systemd を再実装しない理由

PID 1 を作り直しても package/data/fencing/repository/backup の整合性は改善しない。
systemd はローカル process supervisor、cgroup、sandbox、watchdog の実行部として使う。
Mission Core は service contract、semantic health、writer ownership、recovery budget を上位から検査する。

Pacemaker 管理資源について placement/promote/fence の最終決定者は Pacemaker とし、Mission Core が競合する第二 cluster manager にならない。

## Production admission

`MC_Platform_Profile.Qualified_Single_Node` は少なくとも以下を要求する。

- Secure Boot / measured boot / signed kernel modules / lockdown
- runtime integrity appraisal
- SELinux enforcing
- remote audit + immutable receipt
- kdump + remote crash copy + pstore
- hardware watchdog + EDAC/RAS
- healthy/scrubbed storage + protected write path
- trustworthy time + power telemetry
- independent recovery environment
- tested backup restore + off-site backup
- out-of-band management

cluster grade はさらに quorum、fencing、3ノード以上、3 independent fault domains 以上を要求する。

この predicate は外部 subsystem の正しさそのものを証明しない。各 fact の issuer/adapter も qualification 対象である。

## Failure semantics

操作結果は成功/失敗だけではなく **indeterminate** を持つ。external effect の後に応答を失った場合は同じ操作を自動 replay しない。

fault response は概ね:

```text
corrected error -> observe/degrade
persistent error -> drain
write safety risk -> read-only or isolate
old writer uncertain -> fence before promotion
repair -> verify -> soak -> readmit
unknown evidence -> escalate, not autoheal
```

## 本番資格

ソースが豊富であることは production qualification ではない。`MC_Release` は compile/proof/unit/integration に加え power-cut, partition, physical fencing, restore, RAS, time faults, storage faults, Secure/Measured Boot, long soak, update-under-fault まで `Passed` でなければ qualified としない。
