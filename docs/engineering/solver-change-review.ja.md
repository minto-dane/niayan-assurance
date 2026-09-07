# 今回の変更レビュー — Leap / Solver assurance

## 入力と範囲

直前ZIPの5runtime repo/configcore版を入力とした。6つ目のresolvercoreを追加し、
RPMの選択候補生成と信頼判断を分離した。以前の別系統の成果物で上書きしていない。
全source inventory、共有profile、pkgcoreのresolver固定copy、manager実装profileを更新する。

## 修正・検査した意味境界

- 有料SLES profileを有効集合から除外。署名済みでも別baseを受理しない。
- libsolv問題ありtransactionを成功扱いしない。foreign ID/重複/不完全な順序を拒否。
- solverhashの自己申告で元metadataを認証しない。coverageとnative再検査を別にする。
- with/withoutの提供者集合をand/notと混同しない。owner guardと無選択の不正入力も検査。
- 最終状態だけでなく各boundary、属性を含む所有権、操作事前/事後条件、予算を検査。
- 再導入、禁止された初期artifactの除去、保護artifactの保持を区別。
- CNFを完全実行モデルと呼ばない。proofは原CNFを独立再生成しhintの省略を信用しない。
- signed validの後でも期限/排他/bootが変わるため、長い検査の直後に最新状態を再検査。
- 大きなbounded workspaceをruntimeで確保し、失敗をIO_Errorにする。スタックに巨大DBを置かない。
- 提案ELFは非blocking読取り・hash・sealingを行い、hash後の元inode変更を実行へ伝播させない。
- 新profile工具は特殊ファイルを開く前に拒否し、読み取り中の置換/変更を検査。

## 意図的に残した制限

全native source reader・全RPMphase/scriptlet/trigger・他形式adapterは未完。
完全なOS/DB/外部操作のACID、ソルバー最適性、全repoに対するUNSAT、proof済みを宣言しない。
モデル側はUnknown成功を作らず、admission不十分ならdeny。実行層への接続はopt-in。
新しいコード全体の意味的整合を機械証明したわけではない。独立レビュー担当は未割当。

## 開発入口

[統合仕様](specs/solver-assurance.ja.md)、[検証境界](../../../resolvercore/docs/proof-boundary.ja.md)、
[接続条件](../../../resolvercore/docs/integration.ja.md)、[現行機能台帳](specs/capability-matrix.ja.md)。
新しいPython参照試験は有限モデル/工具の検査で、Adaの試験成功ではない。
