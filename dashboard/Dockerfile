FROM python:3.14-alpine
RUN addgroup -g 10001 -S dashboard && adduser -u 10001 -S -G dashboard dashboard
WORKDIR /workspace
ARG VCS_REF=unknown
LABEL org.opencontainers.image.revision=$VCS_REF
COPY --chown=dashboard:dashboard dashboard ./dashboard
COPY --chown=dashboard:dashboard tests ./tests
COPY --chown=dashboard:dashboard .github/workflows ./.github/workflows
COPY --chown=dashboard:dashboard docs/openapi.yaml ./docs/openapi.yaml
COPY --chown=dashboard:dashboard deploy/kubernetes ./deploy/kubernetes
COPY --chown=dashboard:dashboard OPERATIONS.md SECURITY.md ./
USER 10001:10001
ENV DASHBOARD_HOST=0.0.0.0 DASHBOARD_PORT=8080 ZEAZ_ROOT=/workspace ZEAZ_REVISION=$VCS_REF
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/api/health || exit 1
CMD ["python", "-m", "dashboard.api.server"]
