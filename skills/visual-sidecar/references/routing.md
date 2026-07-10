# Routing details

## Decision order

1. No vision provider configured → `doctor`
2. Explicit setup/doctor request → `doctor`
3. UI/design/implementation visual engineering → `front-devwork`
4. General image/OCR/chart/non-UI docs → `vision-recognition`
5. Ambiguous visual request → `visual-sidecar` chooses 3 or 4, never invent pixels

## Anti-overlap

- `doctor` never describes images.
- `vision-recognition` never owns CSS repair loops.
- `front-devwork` never owns receipt OCR as primary task.
- `visual-sidecar` owns unclear routing and config gates.
