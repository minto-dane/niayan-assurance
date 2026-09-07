# E-UNIFIED-1: 統一管理と既存三システムの責任分離

この版は四repo。controlcoreを操作意図/実行受付/結果照合/受入れの管理入口にする。
パッケージの復旧器、サービス管理器、クラスタSDKを独自にコピーしない。
詳細な実仕様は[controlcore architecture](../../../../controlcore/docs/architecture.ja.md)、
[binary contract](../../../../controlcore/docs/protocol.ja.md)、[operations](../../../../controlcore/docs/operations.ja.md)。

## 既存資産に対する変更

MC_Gateのrequests.logは明示provisioningが必要。欠落・空を既存正常状態へ補完しない。
MC_Request_Replayを共有し、gateと読み取り専用receiver観測で同じ履歴規則を使う。
Genesisと通常requestを区別。Known_Failure後に新しいBegunを作るとき、前recordのResultを引き継がずOKへ初期化する。
state executorのreconcileは欠落effects.logを作らない。healing journalは明示provisioningを除き空/欠落を拒否。
他の既存SDKすべてに同じbootstrapを遡及適用したとは主張しない。境界はcapability matrixに残す。

## 管理と復旧

管理器の二者署名planはnative requestの代用品ではない。
Dispatchの前にWALへintentを確定。外部命令の返り値ではなく保護されたreceiver台帳を照合する。
再起動時のOpen/reconcileは命令を出さない。Unknownや失敗はreservationを保持する。
Recovery_Ofは親と同一資源集合・同一clusterで、親をsuspendし、新しい認可と証拠で処理する。
完了の受入れにはOps/Security/Observerの三役とexact reportが必要。親はResolved_Byで閉じ、成功履歴へ改変しない。

## ACID境界

manager WALの整合性はローカル所有者とstorage durabilityを前提とする。
manager logとreceiver logと外部サービスは一つの原子的commitではない。
exactly-once effectsや常時可用性を保証しない。at-most-dispatch管理とnative gate/reconcileによって不確定を封じ込める。
write権限/reader quiescence/データ移行/独立anchorは外部契約を必要とする。

## 分岐統合

最新入力だけを延長すると、過去版の95canonical Ada単位と3testsが消えていた。
別枝から欠落分を復元し、同名の新しい実装は維持した。過去のテストPASSは引き継がない。
[lineage inventory](../../../engineering/lineage-merge.json)が入力ハッシュ・復元・競合を記録する。
復元されたRAS/WLM/HOLD等は既存モデル/SDKの再収録で、現場collectorやdriverの新規完成ではない。

## 成果物の資格

ソース・仕様・試験は同じ版へ束縛するが、これらの存在だけで本番完了にはならない。
現在の実装範囲は[capability matrix](capability-matrix.ja.md)、残作業は[継続計画](continuation.ja.md)。
