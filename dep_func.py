'''
Prints dependency score of repo given package.json in main()
Check to make sure I have proper understanding of '^', '~', and 'x'
Needs more rigerous testing
'''

def get_dep(package):
    # No Dependencies
    if 'devDependencies' not in package.keys():
        return 1
    
    # Classify each dependency as pinned or not_pinned
    pinned = 0
    not_pinned = 0
    for version in package['devDependencies'].values():
        if version[0] == '^':
            # ^ --> pinned if first digit is 0
            if version[1] == '0':
                pinned += 1
            else:
                not_pinned += 1
        else:
            # seperated = [major, minor, version]
            # '^' may be in major element
            seperated = version.split('.')
            if seperated[0][0] == '~':
                # ~ --> Not pinned if only 1 digit
                if seperated[0] == '~0' and seperated[1] == '0':
                    not_pinned += 1
                else:
                    pinned += 1
            else:
                # No special character --> not pinned if major or minor are 'x'
                if seperated[0] == 'x' or seperated[1] == 'x':
                    pinned += 1
                else:
                    not_pinned += 1

    # Avoid divide by 0 if no dependencies (devDependencies maps to empty dict)
    if pinned == 0:
        return 1
    return not_pinned / (pinned + not_pinned)

            
def main():
    # package.json from cloudinary_npm
    package = \
        {
        "author": "Cloudinary <info@cloudinary.com>",
        "name": "cloudinary",
        "description": "Cloudinary NPM for node.js integration",
        "version": "1.27.1",
        "homepage": "http://cloudinary.com",
        "license": "MIT",
        "repository": {
        "type": "git",
        "url": "https://github.com/cloudinary/cloudinary_npm.git"
        },
        "main": "cloudinary.js",
        "dependencies": {
        "cloudinary-core": "^2.10.2",
        "core-js": "3.6.5",
        "lodash": "^4.17.11",
        "q": "^1.5.1"
        },
        "devDependencies": {
        "@types/mocha": "^7.0.2",
        "@types/node": "^13.5.0",
        "@types/expect.js": "^0.3.29",
        "babel-cli": "^6.26.0",
        "babel-core": "^6.26.3",
        "babel-plugin-transform-runtime": "^6.23.0",
        "babel-polyfill": "^6.26.0",
        "babel-preset-env": "^1.7.0",
        "babel-preset-stage-0": "^6.24.1",
        "babel-register": "^6.26.0",
        "babel-runtime": "^6.26.0",
        "date-fns": "^2.16.1",
        "dotenv": "4.x",
        "dtslint": "^0.9.1",
        "eslint": "^6.8.0",
        "eslint-config-airbnb-base": "^14.2.1",
        "eslint-plugin-import": "^2.20.2",
        "expect.js": "0.3.x",
        "glob": "^7.1.6",
        "jsdoc": "^3.5.5",
        "jsdom": "^9.12.0",
        "jsdom-global": "2.1.1",
        "mocha": "^6.2.3",
        "mock-fs": "^4.12.0",
        "nyc": "^13.3.0",
        "rimraf": "^3.0.0",
        "sinon": "^6.1.4",
        "typescript": "^3.7.5",
        "webpack-cli": "^3.2.1"
        },
        "files": [
        "lib/**/*",
        "lib-es5/**/*",
        "cloudinary.js",
        "babel.config.js",
        "package.json",
        "types/index.d.ts"
        ],
        "types": "types",
        "scripts": {
        "test": "tools/scripts/test.sh",
        "test:unit": "tools/scripts/test.es6.unit.sh",
        "test-with-temp-cloud": "tools/scripts/tests-with-temp-cloud.sh",
        "dtslint": "tools/scripts/ditslint.sh",
        "lint": "tools/scripts/lint.sh",
        "compile": "tools/scripts/compile.sh",
        "coverage": "tools/scripts/test.es6.sh --coverage",
        "test-es6": "tools/scripts/test.es6.sh",
        "test-es5": "tools/scripts/test.es5.sh",
        "docs": "tools/scripts/docs.sh"
        },
        "optionalDependencies": {
        "proxy-agent": "^4.0.1"
        },
        "engines": {
        "node": ">=0.6"
        }
        }
    
    print(get_dep(package))

if __name__ == '__main__':
    main()
