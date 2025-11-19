Jasmine Runner Usage
=====================

If you want to test this runner from scratch, start by creating a new jasmine project:

```
% npm install --save-dev jasmine jasmine-json-test-reporter
% npx jasmine init
% npx jasmine example
% git add . && git commit -m "Initial commit"
```

Create spec/helpers/jasmine-json-test-reporter.js
```
var JSONReporter = require('jasmine-json-test-reporter');
jasmine.getEnv().addReporter(new JSONReporter({
	file: 'jasmine-report.json'
}));
```

Record tests
```
BUILD_NAME=jasmine_build
launchable record build --name ${BUILD_NAME}
launchable record session --build ${BUILD_NAME} > session.txt

# Write all tests to a file
find spec/jasmine_examples -type f > test_list.txt

# Run all tests
npx jasmine $(cat test_list.txt)

launchable record tests --base $(pwd) jasmine jasmine-report.json
```

Request subset
```
cat test_list.txt | launchable subset --target 25% jasmine > subset.txt
npx jasmine $(cat subset.txt)
```

