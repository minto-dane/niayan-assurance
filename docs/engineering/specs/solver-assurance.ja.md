> **Nia OS 製品境界**: この文書の旧Leap/SLES/native RPMDB前提は履歴です。現行製品は [Nia構成](../../../../distribution/docs/architecture.ja.md) と [所有権](../../../../distribution/docs/ownership-and-effects.ja.md) を参照。既存部品の安全条件は無効化しません。

# E-SOLVE-1: Leap / 独立解決検査 統合仕様

現行は6つのruntime repository（assurance/pkgcore/statecore/controlcore/configcore/resolvercore）と
配布用distribution workspace。resolvercoreは[形式非依存仕様](../../../../resolvercore/docs/neutral-spec.ja.md)、
pkgcoreは[RPM意味層](../../../../pkgcore/docs/rpm-resolution.ja.md)を持つ。
旧5repo/dual-baseを説明する文書は履歴で、ADR-0035/0036が現行判断。

```text
認証済みrepo/元成果物/設定/実状態
             │                    非特権のlibsolv or CaDiCaL
     正確なnative reader               │
             │                     未信頼の提案
      正規のneutral Universe ───────────┤
             │                          │
       独立意味・順序検査 ◀───────────────┘
             │
    exact physical plan / native全効果の再照合
             │
    最新認可・設定・停止確認・予約・世代・期限
             │
      既存のWAL/CAS/ファイル適用・復旧
```

UNSATは別の診断分岐で、同じUniverseから再生成したCNFに対する証明を検査する。
RUP/RAT列だけで元のmetadata省略や古いsnapshotを正当化しない。

SDKに接続するObserve/Check_Native/Recheck_Currentが未完成なら実行gateは使用しない。
既存workerに最初から全gateが組み込まれたとは言わない。統一missionctl入口も診断専用。
旧直接経路が本番資格化を満たしたという意味ではなく、新required release gatesを満たす
呼出しgraph・権限制御の審査まで必要。管理器を迂回するroot writerは保証範囲外。

この版で増えたものは判断・証明列検査・native投影・提案helper・SDK・診断。
remote management HA、physical fencing、boot installer、全DB移行/restore、完全な
native RPMDB所有権移行、全scriptlet/trigger、独立アンカー、長期GCの未完は残る。
新しい計画検査がACID範囲を広げたわけではなく、既存[ACID境界](acid-contract.ja.md)を維持。
