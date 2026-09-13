#!/bin/bash

# The official SHA-512 checksum (provided by Apache)
EXPECTED_SHA512="C7D7B2318CB51AA0C61D3246A51C349210073C5C9B754947EF965A439F2F939E8600F204E134A75AC31FAF3829C9370960EF7C6A9886C8A1DBF0339A21F4C54C"

set -e

echo "Starting download and verification of Kafka Binary file"

wget -q --show-progress "https://dlcdn.apache.org/kafka/4.3.1/kafka_2.13-4.3.1.tgz" # Main Binary File

wget -q --show-progress "https://downloads.apache.org/kafka/4.3.1/kafka_2.13-4.3.1.tgz.asc" # For GPG 

wget -q --show-progress "https://downloads.apache.org/kafka/KEYS"

# Verify the SHA of binary file

echo "Verifying SHA-512 checksum..."
#cd "${DOWNLOAD_DIR}"

LOCAL_CHECKSUM=$(sha512sum "kafka_2.13-4.3.1.tgz" | awk '{print toupper($1)}')

if [ "${LOCAL_CHECKSUM}" == "${EXPECTED_SHA512}" ]; then
    echo "  ✅ SHA-512 checksum verification: PASSED"
else
    echo "  ❌ SHA-512 checksum verification: FAILED!"
    exit 1
fi
#########################################3

# Verify the PGP of binary file

echo "Verifying PGP signature..."

gpg --import --quiet "KEYS"
# See this URL
# https://downloads.apache.org/kafka/KEYS

if gpg --verify "kafka_2.13-4.3.1.tgz.asc" "kafka_2.13-4.3.1.tgz" 2>/dev/null; then
    echo "  ✅ PGP signature verification: PASSED"
else
    echo "  ❌ PGP signature verification: FAILED!"
    exit 1
fi

echo "------------------------------------------------"
echo "✅ Verifications passed successfully!"
echo "------------------------------------------------"
echo " "
echo "------------------------------------------------"
echo "🚀 Now we will install Java-21 for you bro 🚀"
echo "Since Kafka Needs Java 17+"
echo "------------------------------------------------"

apt update

apt install -y openjdk-21-jdk-headless

echo "------------------------------------------------"
echo "📖 Untar kafka.tgz file"
echo "------------------------------------------------"


echo "------------------------------------------------"
echo "🧹 Now we clean our current directory"
echo "------------------------------------------------"

tar -xvf kafka_2.13-4.3.1.tgz

mkdir download

mv *.* download/

rm KEYS

mv download/kafka_2.13-4.3.1 .

echo "------------------------------------------------"
echo "✅ DONE"
echo "------------------------------------------------"