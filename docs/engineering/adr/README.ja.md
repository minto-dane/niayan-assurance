# 設計判断の索引

状態と置換関係の正本は`assurance/engineering/adrs.json`。独立レビュー待ちを承認済みに読み替えない。通常の製品仕様は現在の採用構成を説明する。

| ADR | 状態 | 置換する判断 |
|---|---|---|
| [ADR-0001: 保証範囲を状態領域ごとに限定する](ADR-0001.ja.md) | proposed-for-review | — |
| [ADR-0002: 三リポジトリと単一の状態所有者](ADR-0002.ja.md) | superseded | — |
| [ADR-0003: 純粋再生コアとI/O境界を分離する](ADR-0003.ja.md) | proposed-for-review | — |
| [ADR-0004: 既存復旧記録を新規作成しない](ADR-0004.ja.md) | proposed-for-review | — |
| [ADR-0005: 確定・復旧の判断根拠を固定する](ADR-0005.ja.md) | proposed-for-review | — |
| [ADR-0006: 履歴のphaseと実像を照合する](ADR-0006.ja.md) | proposed-for-review | — |
| [ADR-0007: 完全レコードと部分末尾を分ける](ADR-0007.ja.md) | proposed-for-review | — |
| [ADR-0008: 診断器を読み取り専用にする](ADR-0008.ja.md) | proposed-for-review | — |
| [ADR-0009: 冪等な再送で回復媒体を枯渇させない](ADR-0009.ja.md) | proposed-for-review | — |
| [ADR-0010: 未知の外部効果を再送しない](ADR-0010.ja.md) | proposed-for-review | — |
| [ADR-0011: quorumと実隔離を代替させない](ADR-0011.ja.md) | proposed-for-review | — |
| [ADR-0012: 信頼・監査をOSの巻戻しから分離する](ADR-0012.ja.md) | proposed-for-review | — |
| [ADR-0013: 回復用データを業務データと混同しない](ADR-0013.ja.md) | proposed-for-review | — |
| [ADR-0014: 復旧予算を永続化して暴走を防ぐ](ADR-0014.ja.md) | proposed-for-review | — |
| [ADR-0015: 共有コード変更を明示した互換変更にする](ADR-0015.ja.md) | proposed-for-review | — |
| [ADR-0016: 開発証跡をsource subjectへ束縛する](ADR-0016.ja.md) | proposed-for-review | — |
| [ADR-0017: 要求・ADR・故障・試験を機械で追跡する](ADR-0017.ja.md) | proposed-for-review | — |
| [ADR-0018: CIを特権運用から隔離する](ADR-0018.ja.md) | proposed-for-review | — |
| [ADR-0019: 起動・ネットワークは独立した回復経路を持つ](ADR-0019.ja.md) | proposed-for-review | — |
| [ADR-0020: 未認定を既定値にする](ADR-0020.ja.md) | proposed-for-review | — |
| [ADR-0021: 統一管理を第4リポジトリへ分離](ADR-0021.ja.md) | superseded | ADR-0002 |
| [ADR-0022: Intent・receipt・業務受入れの三段階](ADR-0022.ja.md) | proposed-for-review | — |
| [ADR-0023: 再送防止台帳の初期化と復旧を分離](ADR-0023.ja.md) | proposed-for-review | — |
| [ADR-0024: 復旧系譜と予約はexact資源集合で管理](ADR-0024.ja.md) | proposed-for-review | — |
| [ADR-0025: 部分tail修復はexact署名と証拠保存後だけ](ADR-0025.ja.md) | proposed-for-review | — |
| [ADR-0026: 共有契約と管理器実装の二つのprofile](ADR-0026.ja.md) | proposed-for-review | — |
| [ADR-0027: 枝分かれした成果物を在庫付きで統合](ADR-0027.ja.md) | proposed-for-review | — |
| [<!-- Superseded by ADR-0036; historical decision, not current authority. -->](ADR-0028.ja.md) | superseded | ADR-0021 |
| [ADR-0029: 設定の意味・優先順位・完全性を分離](ADR-0029.ja.md) | proposed-for-review | — |
| [ADR-0030: NVIDIAは正確なcapabilityと稼働設定で判定](ADR-0030.ja.md) | proposed-for-review | — |
| [<!-- Superseded by ADR-0035; historical decision, not current authority. -->](ADR-0031.ja.md) | superseded | — |
| [ADR-0032: 組立て入力の署名とimage資格化を分離](ADR-0032.ja.md) | proposed-for-review | — |
| [ADR-0033: 設定承認をphase・boot・epochへ束縛する](ADR-0033.ja.md) | proposed-for-review | — |
| [ADR-0034: 内容観測は有界かつ非万能とする](ADR-0034.ja.md) | proposed-for-review | — |
| [ADR-0035: 公開Leap 16.0だけを有効ベースにする](ADR-0035.ja.md) | superseded | ADR-0031 |
| [ADR-0036: 形式非依存の検査器を第6リポジトリへ分離](ADR-0036.ja.md) | proposed-for-review | ADR-0028 |
| [ADR-0037: ソルバーは非特権の未信頼提案器](ADR-0037.ja.md) | proposed-for-review | — |
| [ADR-0038: SATモデル検査とUNSAT証明検査を分離](ADR-0038.ja.md) | proposed-for-review | — |
| [ADR-0039: native意味保存と全効果coverageを別義務にする](ADR-0039.ja.md) | proposed-for-review | — |
| [ADR-0040: 独立proof checkerと証明対象の境界](ADR-0040.ja.md) | proposed-for-review | — |
| [ADR-0041: 長い検査後の生きた認可を再照合](ADR-0041.ja.md) | proposed-for-review | — |
| [ADR-0042: Nia OSの単一供給元とDEB入力](ADR-0042.ja.md) | proposed-for-review | ADR-0035 |
| [ADR-0043: Niaカタログ単独所有と新規導入](ADR-0043.ja.md) | proposed-for-review | — |
| [ADR-0044: DEB意味層と非特権取り込み](ADR-0044.ja.md) | proposed-for-review | — |
| [ADR-0045: 回復ドメイン・暗号化・署名起動](ADR-0045.ja.md) | superseded | — |
| [ADR-0046: 再現性を正確な配布成果物へ拘束](ADR-0046.ja.md) | proposed-for-review | — |
| [ADR-0047: 製品仕様と継承部品契約の階層](ADR-0047.ja.md) | proposed-for-review | — |
| [ADR-0048: XFS永続領域と健全性責任の分離](ADR-0048.ja.md) | proposed-for-review | ADR-0045 |
| [ADR-0049: 実行境界・残余記録・検査ゲートの合成](ADR-0049.ja.md) | proposed-for-review | — |
