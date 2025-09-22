.PHONY: verify run

verify:
	curl -fsS http://localhost:8080/healthz > /dev/null
	curl -fsS http://localhost:8080/readyz > /dev/null
	curl -fsS http://localhost:8080/metrics | grep -q arcanum_requests_total

run:
	uvicorn arcanum.main:app --reload --host 0.0.0.0 --port 8080
