# Piano sviluppi futuri (integrazione con LLM-WikiRace-Benchmark)

## Obiettivo
Portare la teoria del progetto (loop unico + strategie stratificate + controlli di invarianti) in una valutazione **affidabile, riproducibile e comparabile** sul benchmark ufficiale.

## Gap attuali
- Lo script bridge attuale è volutamente minimale e usa un motore deterministico semplice.
- Manca un mapping robusto e testato del `GameState` del benchmark verso lo stato interno.
- Mancano report standardizzati per confrontare mode e costi.
- Manca validazione end-to-end con run reali benchmark-ready.

## Roadmap proposta

### Fase 1 — Stabilizzazione bridge (breve termine)
1. **Compatibilità forte con `GameState` ufficiale**
   - Introdurre adapter esplicito `BenchmarkStateAdapter` con mapping campi dichiarativo.
   - Gestire varianti schema (`outgoing_links`, `links`, ecc.) con fallback documentato.
2. **Contratti d'uscita hardenizzati**
   - Verificare sempre: indice in range, lista output coerente con batch, `usage_data` completo.
   - Telemetria errori parse/shape per ogni batch.
3. **CLI operativa**
   - Aggiungere flag: `--num-games`, `--seed`, `--max-steps`, `--output-json`.

### Fase 2 — Fedeltà alla teoria (medio termine)
1. **Porting logica strategy dal core locale**
   - Estrarre policy condivise (`cycle avoidance`, `budget gating`, fallback deterministico) in modulo riusabile.
   - Evitare duplicazione tra `src/wikirace/strategies.py` e script benchmark.
2. **Replan ed escape nel batch engine**
   - Implementare trigger di replan coerenti con le modalità `stratified`/`full`.
   - Tracciare contatori: replan, trap, fallback, budget rejection.
3. **Opzione Oracle controllata**
   - Valutare integrazione opzionale distance-oracle con chiaro flag “topology-assisted”.

### Fase 3 — Valutazione rigorosa (medio-lungo termine)
1. **Suite esperimenti standard**
   - Matrice fissa: difficulties x modes x seeds x budget.
   - Identico ordine istanze tra modalità.
2. **Reporting comparabile**
   - Generare `summary.json` + CSV tabellare + breakdown per failure reason.
   - KPI: success rate, median steps, p95 steps, fallback/replan rate.
3. **Significatività statistica**
   - CI bootstrap o test proporzioni per confronto mode vs baseline.

### Fase 4 — Produzione/CI (lungo termine)
1. **Workflow CI dedicato benchmark**
   - Job smoke su subset piccolo ad ogni PR.
   - Job full schedulato (notturno) con artifact versionati.
2. **Riproducibilità completa**
   - Pin versioni dipendenze + lockfile.
   - Metadata run: commit SHA, config hash, timestamp UTC, hardware info.
3. **Governance risultati**
   - Policy esplicita: niente claim di improvement senza run full + report allegato.

## Deliverable concreti (ordine consigliato)
1. `src/wikirace/benchmark_adapter.py` (mapping robusto stato benchmark)
2. `tests/test_benchmark_adapter.py` (contratti input/output)
3. `scripts/run_benchmark_batch_eval.py` v2 (flag estesi + logging strutturato)
4. `scripts/aggregate_benchmark_results.py` (report JSON/CSV)
5. workflow CI benchmark smoke

## Criteri di accettazione
- Esecuzione batch senza errori shape su almeno 3 seeds per difficulty.
- Output confrontabile cross-mode su stesso set istanze.
- Report automatico con KPI + failure taxonomy.
- Ripetibilità: stessi risultati (entro tolleranza) con seed fisso.
