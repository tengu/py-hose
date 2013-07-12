
all:

clean:
	rm -fr *.egg-info dist build *.egg *.pyc
scrub: clean
	rm -fr $(ve)
push:
	python setup.py register sdist upload

#ve_opt=--system-site-packages
ve=$(PWD)/ve
python=$(ve)/bin/python
ve: $(ve)
$(ve):
	virtualenv $(ve_opt) $@

install: $(ve)
	$(python) setup.py install
test: $(ve)
	$(python) setup.py test
develop:
	$(python) setup.py develop

example:
	$(python) test.py example

### scratch


s:
	curl -s https://api.github.com/legacy/repos/search/pipeline

p:
	curl -s https://github.com/basho/riak_pipe | tee x.project.json
pp:
	curl -s https://api.github.com/repos/basho/riak_pipe/subscribers | tee x.subs.json

t:
	python example.py

tt:
	cat x.cache/67e2e9b4d4787e1a314d07a63fb13bfb \
	| jq -M -r '.repositories[] | "https://api.github.com/repos/\(.owner)/\(.name)/subscribers" '

test_% :
	python test.py TestHose.$@

ttt:
	cat data/search-result.json \
	| tr '\n' ' ' \
	| jq -M .

t4:
	echo 'foo\nfoo\nbar' | sort | uniq -c | sort -nr | awk '{ print $$1 "\t" $$2 }'
