# 変更レビュー — SUSE16 / configuration integrity

独立レビュー待ち。意味的完全性の証明ではなく、今回確認した設計境界の記録。

|確認|対処|残る条件|
|---|---|---|
|古い設定の単純保持|旧vendor/local/newvendorの三方向と削除・追加|native serializer・完全inventory|
|候補と実行中の混同|phase別receipt、bootとtargetの拘束|実観測と作用の認証接続|
|SUSEとFedoraの混在|別family profileとsigned snapshot|SUSE実機・package closure|
|架空KIWI version属性|snapshot固定、正規schema要素のみ生成|実schema/build/boot検査|
|全ソフト対応と表示する危険|unsupportedを明示、coverage catalog|すべての対象adapter実装|
|危険なnative config命令|制限parserがinstall等を拒否|元文法を安全に扱う別adapter|
|署名が意味の正しさだという混同|diagnostic always execution_permit=false|資格化された独立validator/observer|
|partial parser失敗が成功扱いになる経路|line内のlocal statusと外側のinvalid statusを分離|Ada実行試験|
|旧boot観測の再使用|explicit authorized rebind + runtime再検査|実reboot故障試験|
|メタデータの外部location/DTD|offline安全解析、hash・byte集合検査|元のrepository/RPM署名とresolver|
|5repoへ増えてCIが4のまま|契約・試験・build・文書・配布在庫へ追加|Ada全単位のコンパイル|
|全体ACIDの誤称|独立した耐久境界とunknown効果の照合|nativeDB/外部効果の統合|

過去の証跡を現行版PASSへ転記しない。新しいsource-bound evidenceを別のディレクトリへ保存する。
