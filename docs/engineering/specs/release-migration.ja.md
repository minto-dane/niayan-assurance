# 仕様 E-MIG-1: リリースと永続状態の移行

## 世代を混同しない

source subject、共有contract profile、wire schema、永続schema、package generation、boot identity、trust epochは別です。
この版では共有source profileが変わります。古いpolicyを新コードに無条件で流用しません。
既存のファイルlog形式はMCLOG002を維持しますが、解釈を厳しくしています。

## 今回の非互換な受入れ条件

commit中またはrestore中にreceiptが変わる履歴、done領域と異なる実像、protected rootそのものへの計画は新readerで拒否します。
旧readerが過去に作った可能性がある状態を、本番で自動修正して移行しません。
まず原本と全参照CAS、旧toolchain/binary/config/profile、回復鍵の使用経路を固定して保持し、読み取り専用で棚卸しします。
作業停止と互換性確認なしに旧readerを削除しないでください。

## 配布の順序

1. 開発/統合でsource・tests・proof・target証拠を揃える。
2. 書き込みを止める範囲、旧状態、未解決操作、rollback/data compatibilityを確定する。
3. カナリアで更新し、実行版と導入版、構成と業務、復旧を確認する。
4. 関連するproducer/consumerとprofile/authorityを明示的な手順で切り替える。
5. 安定観測後に受け入れる。保留復旧や保持契約が残る間は古い部品をGCしない。

## リリースゲート

不明・失敗・未実施を区別し、独立した承認者がsource/binary/profile/platform/policyを同時に確認します。
失敗したgateを`continue-on-error`相当で通さない。緊急修正でも適用対象を狭め、検査・署名・auditを解除しません。
アプリデータの非互換な移行はパッケージundoとは別の計画を必要とします。

## 状態GC

この版は自動GC/全ジャーナル圧縮を追加していません。pin、accepted generation、復旧中操作、監査、保持法令、バックアップ祖先を横断する設計が必要です。
空き容量を得るために未解決logを消す運用は禁止です。容量不足は新規変更を停止し、専用の保持/増設計画へ送ります。

## Unified-management版の追加互換性条件

四repoへ移行。requests.logは新規genesisが必要で、欠落/空を既存状態として開けません。
healing journalは明示provisioning以外の自動作成を拒否。古い配備手順のmkdir/touchだけでは不十分です。
新管理器はshared profileとimplementation profileを両方固定し、旧profileのdispatchを拒否します。
historical policyをCASで保持しreplayしますが、新しい操作/closureは現在policyとの一致を要求します。
旧planが期限切れ・policy変更の場合、元の履歴は編集せず、同一資源集合を持つ新recovery planへ移します。
元が正常でも旧profile readerでの再現確認を終える前に古いbinary・policy・CAS・requestを削除しません。
