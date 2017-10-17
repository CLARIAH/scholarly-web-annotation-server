all: test_server test_client

test_server:
	python -W ignore -m unittest discover
	# the -W ignore is to get rid of ResourceWarnings
	# for elasticsearch sockets when errors are raised in tests

test_client:
	npm run test

