API_BASE = 'https://dweb-search-api.anwen.cc';
CLIENT_ID = 'b597886a5fe361255e03';

document.addEventListener("DOMContentLoaded", pagePrepare);
document.getElementById("submit_metadata").addEventListener("click", submitMetadata);
document.getElementById("add_metadata").addEventListener("click", toggleAddMetadata);
document.getElementById("submit_search").addEventListener("click", submitSearch);

var getCookiebyName = function (name) {
  var pair = document.cookie.match(new RegExp(name + '=([^;]+)'));
  return !!pair ? pair[1] : null;
};

function pagePrepare() {
  // get params
  const url = window.location;
  let searchParams = new URLSearchParams(url.search);
  var github_code = searchParams.get("code");
  handleOauth2(github_code, github_code);
  var question = searchParams.get("q");
  if (question!=null) {
    getSearchResults(question);
  }
  document.getElementById("question")
      .addEventListener("keyup", function(event) {
      event.preventDefault();
      if (event.keyCode === 13) {
          document.getElementById("submit_search").click();
      }
  });
}

function handleOauth2(github_code, github_code) {
  if (getCookiebyName('access_token') == null && github_code != null) {
    axios.get(API_BASE + '/proxy', {
        params: {
          client_id: CLIENT_ID,
          code: github_code
        }
      })
      .then(function (response) {
        // TODO: handle errors
        access_token = response['data']['access_token'];
        document.cookie = "access_token=" + access_token;
        document.getElementById("github_auth").style.display = "none";
        document.getElementById("add_metadata").style.display = "block";
      })
      .catch(function (error) {
        console.log(error);
      })
      .then(function () { // always executed
        window.history.replaceState({}, document.title, url.pathname);
      });
  }
  if (getCookiebyName('access_token') != null) {
    document.getElementById("github_auth").style.display = "none";
    document.getElementById("add_metadata").style.display = "block";
  }
}

function toggleAddMetadata() {
  if (document.getElementById("add_metadata_form").style.display == "block") {
    document.getElementById("add_metadata_form").style.display = "none";
    document.getElementById("results").style.display = "block";
  } else {
    document.getElementById("add_metadata_form").style.display = "block";
    document.getElementById("results").style.display = "none";
  }
}

function submitMetadata() {
  var title = document.getElementById("title").value;
  var cid = document.getElementById("cid").value;
  var url = document.getElementById("url").value;
  var license = document.getElementById("license").value;
  var filetype = document.getElementById("filetype").value;
  var tags = document.getElementById("tags").value;
  
  var summary = document.getElementById("summary").value;
  var author_name = document.getElementById("author_name").value;
  var author_url = document.getElementById("author_url").value;
  var author_wallet = document.getElementById("author_wallet").value;
  var data_cid = document.getElementById("data_cid").value;
  var miner_ids = document.getElementById("miner_ids").value;

  var author = {};
  if (author_name) {
    author.name = author_name;
  }
  if (author_url) {
    author.url = author_url;
  }
  if (author_wallet) {
    wallet = {}
    _wallet = author_wallet.split(';');
    for (var i =0; i < _wallet.length; i++) {
      kv = _wallet[i].split(':');
      wallet[kv[0]] = kv[1];
    }
    author.wallet = wallet;
  }
  axios.post(API_BASE + '/share', {
      title: title,
      id: cid,
      url: url,
      license: license,
      filetype: filetype,
      tags: tags,
      summary: summary,
      authors: [author],
      data_cid: data_cid,
      miner_ids: miner_ids,
    }, {
      headers: {
        Authorization: 'token ' + getCookiebyName('access_token')
      }
    })
    .then(function (response) {
      if ("data" in response['data']) {
        alert('Success!');
      }else if ("error" in response['data']) {
        alert('ERROR: '+ response['data']['error']);
      }
      console.log(response);
    })
    .catch(function (error) {
      console.log(error);
      alert('ERROR: '+ error);
    })
    .then(function () { // always executed
    });
}

function submitSearch() {
  document.getElementById("add_metadata_form").style.display = "none";
  document.getElementById("results").style.display = "block";
  var question = document.getElementById("question").value;
  getSearchResults(question);
}

function getSearchResults(question) {
  results = document.getElementById("results");
  results.innerHTML = '';
  axios.get(API_BASE+ '/search', {
      params: {
        question: question,
      }
    })
    .then(function (response) {
      data = response['data']['items'];
      if (data.length==0){
        arr0 = ['<div class="webResult">',
          'No result.',
          '</div>'
        ];
        results.innerHTML += arr0.join('');
      }
      for (var i =0; i < data.length; i++) {
        r = data[i];

        // id could be ipns or ipfs, sometimes, it is still http(s)
        hash = r.id.split('://')[1]
        if (r.id.startsWith('ipfs://')){
          hash = 'ipfs/'+hash
        } else if (r.id.startsWith('ipns://')){
          hash = 'ipns/'+hash
        } else {
          hash = ''
        }
        see_also = ['See also: &nbsp;']
        if (hash!=''){
          see_also.push('<a href="https://ipfs.io/', hash, '" target="_blank">gateway1</a>&nbsp;');
          see_also.push('<a href="https://ipfs.fleek.co/', hash, '" target="_blank">gateway2</a>&nbsp;');
        }
        if (r.url && r.url.startsWith('http')){
          see_also.push('<a href="', r.url, '" target="_blank">HTTP</a>&nbsp;');
        }
        see_also = see_also.join('');
        tags = '';
        if (r.tags.length>0) {
          tags += 'Tags: ';
        }
        for (j = 0; j < r.tags.length; j++) {
          tag = r.tags[j];
          tags += '<a href="?q='+tag+'" target="_blank">'+tag+'</a>&nbsp;';
        }

        license = '';
        switch (r.license) {
          case 'CC0':
            license = 'License: <a href="https://creativecommons.org/publicdomain/zero/1.0/" target="_blank">CC0: Public Domain</a>';
            break;
          case 'CC-BY':
            license = 'License: <a href="https://creativecommons.org/licenses/by/4.0" target="_blank">CC BY 4.0</a>';
            break;
          case 'CC-BY-SA':
            license = 'License: <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank">CC-BY-SA 4.0</a>';
            break;
          case 'CC-BY-ND':
            license = 'License: <a href="https://creativecommons.org/licenses/by-nd/4.0/" target="_blank">CC-BY-ND 4.0</a>';
            break;
          case 'CC-BY-NC':
            license = 'License: <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC-BY-NC 4.0</a>';
            break;
          case 'CC-BY-NC-SA':
            license = 'License: <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank">CC-BY-NC-SA 4.0</a>';
            break;
          case 'CC-BY-NC-ND':
            license = 'License: <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank">CC-BY-NC-ND 4.0</a>';
            break;
          default:
            if (r.license) {
              license = r.license // TODO
            }
        }
        license += '&nbsp;';

        authors = ''
        if (r.authors.length>0) {
          authors += 'Authors/Curators: ';
        }
        for (j = 0; j < r.authors.length; j++) {
          author = r.authors[j];
          authors += '<a href="'+author.url+'" >'+author.name+'</a>&nbsp;';
          if (author.wallet){
            authors += 'support via: ';
            if (author.wallet.likeid){
              authors += '<a href="https://like.co/in/widget/pay?to='+author.wallet.likeid+'&amount=1&remarks=support~'+r.id+'" target="_blank">likeid</a>&nbsp;';
            }
            if (author.wallet.filecoin){
              authors += '<span onclick=show_qr("'+author.wallet.filecoin+'","qrcode'+j+'") >FIL <span style="display: inline-block;" id="qrcode'+j+'"></span></span>';
            }
          }
          if (j < r.authors.length-1){
            authors += ';&nbsp;';
          }
        }
        if (r.id.includes('wikipedia-on-ipfs.org')){
          authors += 'support via:  <a href="https://bitpay.com/464448/donate" target="_blank">bitpay</a>&nbsp;';
        }
        // dataset_filecoin_info
        dataset_info = '';
        if (r.filetype!=null && r.filetype!="html") {
          dataset_info += ' Filetype: ' + r.filetype;
        }
        if (r.data_cid!=null && r.data_cid!="") {
          dataset_info += ' dataCid: ' + r.data_cid;
          dataset_info += ' MinerIDs: ' + r.miner_ids.join(', ');
          dataset_info = '<p>' + dataset_info + '</p>';
          dataset_info += '<p>download via: <code>lotus client retrieve --miner=minerid dataCid filename.filetype</code></p>';
        }
        arr = ['<div class="webResult">',
          '<h2><a href="', r.id, '" target="_blank">', r.title, '</a></h2>',
          '<p><a href="', r.id, '" target="_blank">', r.id, '</a></p>',
          '<p>', r.summary, '</p>',
          '<span>', see_also, tags, license, authors, '</span>',
          dataset_info,
          '</div>'
        ];
        results.innerHTML += arr.join('');
      }
    })
    .catch(function (error) {
      console.log(error);
    })
    .then(function () { // always executed
    });
}

function show_qr(text, eleid) {
  ele = document.getElementById(eleid);
  if (ele.innerHTML!=''){
    ele.innerHTML='';
  } else{
    var qrcode = new QRCode(ele, {
      text: text,
      width: 128,
      height: 128,
      colorDark : "#000000",
      colorLight : "#ffffff",
      correctLevel : QRCode.CorrectLevel.H
    });
  }
}
