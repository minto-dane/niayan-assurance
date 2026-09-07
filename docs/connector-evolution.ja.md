# 接続契約の変更を安全に扱う

共有Ada sourceは各repoの`vendor/contracts`へ固定コピーされます。`ci/check-contract.sh`はmanifestの厳密な形式・順序・重複と実file集合を照合し、改変、欠落、未知ファイル、symlink、special fileをビルド前に拒否します。`contracts.source.sha256`と実行可能な`Contract_Lock`表は同じ集合を表します。

実行時は`MC_Contract_Profile.Fingerprint`をsite policyのContractと比較します。定義は `SHA256(ASCII "MISSION-CORE-SHARED-SOURCE-PROFILE-v1\n" || contract-profile.source.sha256 の正確なbytes)` です。入力は共有src/runtime全Ada（生成したprofile自身のみ除外）の、pathでsortしたsha256sum形式です。循環するhashではありません。

このprofileはソース変更で旧policyを拒否する粗い互換性ロックです。暗号署名・形式証明・再現可能build証明・native tool/libraryの完全な依存封鎖ではありません。privateなPkg/Stateの意味変更は別途semantic reviewと試験が必要です。profileが一致するだけで、新旧のあらゆる操作が互換とは判定しません。

## 変更手順

1. wire/state永続形式と意味を変更するか分類し、未認識field/versionをどう拒否するか規定する。曖昧な下位互換を作らない。
2. shared sourceを変更し、全対応ベクタ・否定試験・永続record回復試験を更新する。必要ならmagic/majorを変更する。
3. 生成profile、source manifest、Contract_Lock表、vendor固定コピーを同一変更で更新する。生成の定義をレビューし、元配布物/署名を別の信頼経路で確認する。
4. 各repoを独立にcompile/test/flow/proveし、`ci/cross-repository.sh`で実行ファイル間を検査する。旧request/旧profile/不正署名/未知fieldを拒否する試験を含める。
5. site authorityが新source profileに対応するpolicyを明示再発行する。未解決intentがある場合は互換な旧復旧器を保持し、gateやjournalを初期化して強行しない。

この版は無停止の鍵/契約自動切替を完成させたものではありません。version/profile変更による意図的停止を本番で無計画に起こさないよう、旧復旧経路・承認高水位・失効情報を保全した保守手順を検証する必要があります。

## 署名の役割

要求者とSemantic_Healthの観測者は別鍵にします。site policyは要求鍵をいずれかのobserver鍵と共有する設定を拒否します。同じ秘密を別名にしただけでは分離ではありません。複数observer相互の独立性はsite責任です。

署名domainは`MC-HEALTH-v1`、request/witnessは既存v2の別domainです。署名入力は`u16be(domain length)||domain||canonical bytes`です。`verify-health-report`CLI単体は暗号/形式の確認のみで、鮮度やsite role、物理的事実を承認しません。workerはその追加条件を検査します。

fixture鍵・fixture署名は公開された試験用です。`fixtures/test-*.pub`をproduction policyへ入れないでください。
