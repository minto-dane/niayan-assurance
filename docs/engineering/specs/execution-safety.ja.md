# 実行境界・永続化・再開の契約

状態: 仕様と対応するAda/SPARKソース。Ada実行・形式証明・ターゲット受入は未完。

## 1. 対象と責任

Niaの公開管理入口は`nia`。供給元は固定したDebian 14 Forky、入力DEB、内部正本はNia catalog、永続領域はXFSとする。六つのコードベースとdistributionの責任分割は維持する。実行計画、停止状態、設定、依存解決、回復可能性のどれかを署名一つで代替してはならない。

`Pkg_Managed_Engine`は、元の認可、停止確認、設定証拠、独立解決検査、native意味／物理計画照合を重ねる接続SDKである。必須callbackをすべて指定する。下位の弱いEngineはパッケージ本体内に隠す。長時間の解決検査の後にも、元の認可・停止状態・設定・現在の予約を再検査する。

これは既存`pkg_worker`へ自動接続したことを意味しない。旧workerを保護済み本番入口として公開しない。配備する実行ファイルについて、次の接続表を現場で埋め、否定試験を通す必要がある。

| 境界 | 必須条件 |
|---|---|
| 入力 | 元バイト列の真正性、全依存・設定・副作用入力の閉包 |
| writer | すべての検査と変更を通して同じ排他的予約を保持 |
| 設定 | 観測範囲・読み込み順・生成物・稼働状態の適格なobserver |
| 停止 | 全対象・受付・結果不明操作・必要な外部隔離の照合 |
| 提案 | solver出力を独立に検査し、元形式にも直接照合 |
| 実変更 | 正確なplan、保存済み原本、予算、ログ、現在の権限 |
| 完了 | receiver台帳と実状態、業務健全性の別々の確認 |

モデル内の`Generation`はcatalog/imageの版であり、cluster membership epochではない。native verifierがそのモデルとsource集合・変更方向を結び、元の認可がcluster epochとfenceを検査する。二つの数値が偶然一致しても、証拠の対応は成立しない。

## 2. 外部プロセスの所有

`MC_Command`はLinux/glibc x86-64の境界である。固定ELFをFDで開き、内容・属性を検査し、固定した環境と引数で起動する。shell、継承環境、setuid遷移は使わない。ELF・loader・依存ライブラリの書き込み管理は別途必要であり、FDを保持するだけで内容が凍結したとはしない。

呼出しプロセスは単一threadで、独立reaperを持たず、`MC_Runtime.Initialize`を子生成前に実行する。SIGCHLDの自動回収を許さない。pidfdでleader終了を観測し、leaderを回収する前にそのprocess groupを終了させる。通常終了もgroup cleanupの対象である。stdin/out/errが閉じていた場合にも、fd 0..4への複製が元FDと衝突しないよう事前に高位FDへ置く。

入出力が閉じても期限は残る。出力上限を超えた結果を、切り詰めた正常出力として返さない。終了待ちは通常期限に最大1秒のcleanup余裕を加える。SIGKILLでも終了しないuninterruptible I/Oは結果不明であり、supervisorと現場隔離が担当する。

Process groupの終了は資源の静止証明ではない。helperのdaemon化・別sessionへの脱出は禁止し、配備側は単一cgroupの管理、資源制限、子孫終了の観測を用意する。外部へ送信済みのetcd／service／DB操作は、helper終了後も継続し得る。remote effectの成否はrequest IDと独立した実状態から照合する。

## 3. 観測するファイル

パスの事前情報、開いたFD、読み取り後のFD、最終パスを照合する。inode・mount・size・mode・owner・mtimeに加えctimeを観測する。ctimeは復元対象の属性ではなく、同一inodeへの書き込みや属性変更を検出する手掛かりである。元mtimeへの書き戻しだけで観測を再利用しない。

これは無制限のroot writer、悪意あるkernel、改ざんされたハードウェアを排除する証明ではない。署名原本のhash、書き込み経路の制御、XFS構造検査、アプリケーションデータ整合性は別々に必要である。観測途中に差異を検出した場合、取得した不完全な情報をplanとして公開しない。

## 4. ログの余力

新規intentの前に、そのintentが発生させる終了記録の論理余力を確保する。`MC_Journal_Budget.Fits`は減算の順序を固定してoverflow/underflowを避ける。残レコード数は空きdisk blockやinodeではないため、後者も独立に予約・観測する。

統一管理ログは各planについて未開始stepに3、送信済みに2、結果不明に1、終端に0を残し、未完planにさらに2の余力を保持する。既存の全未完planの予約を新規plan admissionへ加える。確定済みの不明状態を同じ不明状態として観測しただけなら記録を増やさない。新たな情報・解決証拠は通常どおり記録する。

receiver台帳は通常の新規要求で8記録、回復系で4記録を要求する。これはboundedな完了と一回の回復／修復余力であり、無限の再試行を保証しない。部分末尾を修復する前にも修復記録の余力を検査する。既存の満杯台帳へmagicな空きを作る手段ではない。

容量不足で完了記録の保持を諦めたり、過去の再送記録を削除して継続したりしない。管理storeの保持plan数128とevent数65,536は有効な制限である。checkpoint、antirollback、GC、参照の閉包を結ぶ長期運用経路が完成するまで、到達前に新規変更を停止し管理者へ通知する。

## 5. lockとbootstrap

既存のroot・policy・control・checkpoint・network状態へアクセスする経路で、lock inodeを再作成しない。欠落は状態破損として扱う。明示した初期化だけが作成する。古いwriterが元inodeを保持しているかもしれないため、欠落lockを`touch`して復旧したことにしてはならない。

CASは`MC_Store.Initialize`だけが空の私有領域を初期化する。既存storeのOpenはlock・objects・incoming・pinsを作り直さず、不在を破損として扱う。CLIの`pkgctl provision-store`は明示bootstrap専用である。storeから返すバイト列を、その読み取り後にも期待hashと照合する。初期化途中の失敗は状態を残し、稼働領域を再初期化して隠さない。full-root assemblerや全bootstrap運用の接続は未完であり、既存稼働環境の復旧へ混用しない。読取専用診断が新しい管理状態を作成しないことも接続試験の対象にする。

## 6. 証明・試験の境界

SPARK unit、契約、ref model、Python/native probe、Ada実行、GNATprove、target crash試験を区別する。`runtime/`はAda FFIでSPARK_Mode Off。process lifecycleとstatxのPython probeはLinuxと開発runnerを実行するが、Ada版の代わりではない。全体ACID、exactly-once external effect、全障害からの復旧は宣言しない。

一次資料:
- https://man7.org/linux/man-pages/man2/pidfd_open.2.html
- https://man7.org/linux/man-pages/man2/waitid.2.html
- https://man7.org/linux/man-pages/man2/statx.2.html
- https://man7.org/linux/man-pages/man2/fsync.2.html
