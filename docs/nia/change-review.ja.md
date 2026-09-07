# Nia OS 統合変更レビュー — 2026-09-07

## 決定
供給元はDebian 14 Forky fixed snapshots、入力DEB。Niaカタログ単独所有。RPM/Zypper/dpkg互換管理DBは製品の目標ではない。6つのランタイムrepoを保ち、製品規範はdistribution/profiles/nia-os.jsonとdistribution/docsへ集約した。

## 変更
旧distributionをhistory/leap16へ保存。公式archive chainとSourcesを実検査するoffline工具、DEB tar/control inventory、candidate catalog、再現receipt、strict profile/state-domain validatorを追加。Pkg_Deb_Versions/Pkg_Deb_Semanticsを追加。libsolvは明示DEB modeの非特権提案器、neutral resolverは変更しない。Nia名の保護pathをfile planへ追加。niaをmissionctlの入口として追加。first-party executable配布台帳をNia DEB inputへ更新。

## 意味上の注意
`Replaces`は自動overwrite許可でない。全final dependencies一致はPre-Dependsのconfigure段階の証明ではない。`Multi-Arch:any`をforeign指定だけで許可しない。amd64/allで同名binaryを二重導入しない。byte再現は安全なsourceやmaintainer効果の証明でない。旧キーフィンガープリントへrollbackしない。

## 文書の優先順位
製品仕様→参照する部品契約→履歴。これは既存部品の安全ガードを弱める優先順位ではない。Nia/旧部品で前提が違う箇所は統合未完として残す。例: AppArmorの実admission、root最終executor、nativephase lowering。所有権移行不要は、その実装済みを意味しない。

## 検証
最新のevidence/nia-osだけが今回の試験。旧evidenceはhistory-evidenceへ分離。Pythonの実署名fixtureとdpkg比較はAda実行・証明でない。libsolvはmock APIのみ。ソース参照の整合は意味的同値の形式証明でない。ADRはproposed-for-reviewで独立承認を偽らない。
