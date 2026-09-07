# 配置プロファイル（自動導入しない）

このディレクトリは配備レビューの入力です。実際の本番機へ配置・enableする自動スクリプトは含みません。
ビルド済みワーカー、固定済みネイティブ依存関係、受信policy、鍵、権限、サイト観測器、クラスタRBAC、
バックアップが認定された後に、各サイトの構成へ置き換えてください。

## プロセス分離

- 非特権ステージャー: 外部RPMを取得・検査・展開。鍵の取得元/更新を別権限で管理する。
- パッケージワーカー: ネットワーク禁止。受信spool/policyはread-only、専用root/state/store/ledgerだけ変更可能。
- 状態ワーカー: 固定systemctl/Pacemakerのみ。状態所有者を統一し、任意シェル、バイナリ、引数を受理しない。
- 観測者: reservation/quiescence/health/compatibility/isolationで鍵と責任を分離する。署名権限とデータを観測する経路も保護する。
- 配送: 認証済みSSHまたはmTLS等を別途構築し、受信側0700spoolへ原子的に配置。公開HTTPの管理口は設けない。

## systemdのハードニング審査項目

NoNewPrivileges、LimitCORE=0、UMask=0077、ProtectSystem=strict、ProtectHome、PrivateTmp、
RestrictSUIDSGID、必要最小限のAddressFamily/Capability、限定ReadWritePathsを対象にします。
作成したsystemdユニットが実際のsystemd/libc/native-tool動作と合うかを検証してください。
`MemoryDenyWriteExecute`やsyscall filterのようにnativeライブラリや必要機能へ影響する設定は、
互換性を検証してから採用します。試験失敗時に一括で無効化しません。

パッケージワーカーとサイト観測者の秘密鍵を同じサービスへ渡しません。
クラスタ所有サービスの再起動をsystemdとPacemakerの双方が独立に決める構成を作りません。

## 認定記録の必須項目

OS/kernel/glibc/filesystem/device firmware、GNAT/runtime/prover、native libsとELF、MAC policy、
実行UID/能力、RPM署名鍵・authority keys・有効期限、クラスタ構成/障害領域、etcd restore方針、
データ複製/バックアップ/RPO/RTO、試験と復旧演習の結果。

信頼済み更新に見せるためのテスト秘密鍵や「検証済み」フラグは提供しません。
