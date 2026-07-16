import argparse

from app import db
from app.services import TriageService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Processa um arquivo de log de seguranca em lote e imprime a triagem."
    )
    parser.add_argument("--file", required=True, help="Caminho do arquivo de log")
    args = parser.parse_args()

    db.init_db()
    service = TriageService()

    with open(args.file, encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]

    print(f"Processando {len(lines)} eventos de '{args.file}'...\n")
    counts: dict[str, int] = {}
    for line in lines:
        result = service.analyze(line)
        counts[result["classification"]] = counts.get(result["classification"], 0) + 1
        print(
            f"[{result['classification']:8s}] ({result['engine']:>18s}) "
            f"{result['summary']}\n"
            f"             -> acao sugerida: {result['suggested_action']}\n"
            f"             -> log original : {result['log_line']}\n"
        )

    print("Resumo:")
    for classification, total in counts.items():
        print(f"  {classification}: {total}")


if __name__ == "__main__":
    main()
