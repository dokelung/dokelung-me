# dokelung-me
blog content

# How to build this site (note for myself)

```sh
# make main directory
$ mkdir dokelung.me
$ cd dokelung.me

# clone blog contents from this repo "dokelung-me"
$ git clone https://github.com/dokelung/dokelung-me.git

# clone pelican theme from repo "jojo"
$ git clone https://github.com/dokelung/jojo.git

# clone all pelican plugins from repo "pelican-plugins"
$ git clone --recursive https://github.com/getpelican/pelican-plugins

# clone github static site repo "dokelung.github.io" as main output directory
$ cd dokelung-me
$ git clone https://github.com/dokelung/dokelung.github.io.git

# make an test output directory
$ mkdir test-output

# generate site for testing
$ pelican content -o test-output -s pelican.conf
$ cd test-output
$ python3 -m pelican.server # then open browser and goto "localhost:8000", stop with CTRL+C

# generate real site
$ pelican content -o dokelung.github.io -s pelican.conf
$ cd doeklung.github.io
$ git add .
$ git commit -m "update site"
$ git push
```