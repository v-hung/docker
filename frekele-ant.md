### linux

`docker run -v $(pwd):/workspace -w /workspace frekele/ant ant`

### window

`docker run --rm -v "${PWD}:/workspace" -w /workspace frekele/ant ant`
`docker run --rm -v "${PWD}:/workspace" -w /workspace frekele/ant ant -f custom.xml`
