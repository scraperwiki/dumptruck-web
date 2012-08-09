. ../dumptruck_web.sh

setup() {
  export QUERY_STRING='foo=bar'
}

runtests() {
  assert 'aoeaue' false
}
