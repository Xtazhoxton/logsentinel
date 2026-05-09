from logsentinel_sdk import Logger, generate_sentinel_id

def handler(event: dict, context: object) -> dict:
    sentinel_id: str = event.get("sentinel_id") or generate_sentinel_id()

    with Logger(service="e2e-test", sentinel_id=sentinel_id) as logger:
        logger.debug("handler invoked", trigger="manual", env="e2e")
        logger.info("processing started", item_count=3, source="e2e-run")
        logger.info("step completed", step=2, duration_ms=42)
        logger.warning("quota threshold reached", used=80, limit=100)
        logger.error("simulated failure", error_code="E2E_SENTINEL", retryable=False)

    return {"sentinel_id": sentinel_id}
