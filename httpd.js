var express = require('express');
var bodyParser = require('body-parser');
var axios = require('axios');

const port = 19987

var app = express();

app.use(express.static('./dist')) /* for /foo (after rewriting) */
app.use(bodyParser.json())
console.log('Listening on port ' + port)
app.listen(port)

app.get('/query', function (req, ret) {
  const query = req.query.q
  const page = req.query.p
  axios.post('http://127.0.0.1:19986', {
    'q': query, 'p': parseInt(page)
  }).then(function (res) {
    ret.json(res.data)
  }).catch(function (err) {
    console.log('error', err.code)
    ret.json({
      "cur_page": 0,
      "tot_page": -1,
      "list": []
    })
  })
})

process.on('SIGINT', function() {
  console.log('')
  console.log('Bye bye.')
  process.exit()
})
