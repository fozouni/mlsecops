# Stage 1: Builder
FROM python:3.13 AS builder

WORKDIR /build

# Simulate creating an artifact during the build
RUN echo "Hello from the builder stage!" > report.txt


# Stage 2: Final Runtime Image
FROM dhi.io/python:3.13 

WORKDIR /app

# Copy only the artifact from the builder stage
COPY --from=builder /build/report.txt ./report.txt

# Display the file when the container starts
CMD ["cat", "/app/report.txt"]