<template>
<v-app light>

<v-toolbar>
  <v-text-field prepend-icon="search" v-model="qry" v-on:keyup.13="on_search(1)">
  </v-text-field>
  <v-spacer></v-spacer>
  <v-btn color="warning" @click="on_search(1)">search</v-btn>
</v-toolbar>

<div>
<v-alert :value="tot_page < 0" type="error">
  Opps, something goes wrong...
</v-alert>
<v-alert :value="tot_page == 0 && !firing && fired" type="warning">
  No search result.
</v-alert>
<v-alert :value="firing" type="info">
  Searching...
</v-alert>
</div>

<div class="hit" v-for="j in list">
<v-card>
  <v-card-title>
    <a :href="openlink(j.path)" target="_blank" v-if="j.path_highlight.length > 0"
       v-html="j.path_highlight"></a>
    <a :href="openlink(j.path)" target="_blank" v-else>{{j.path}}</a>
    <v-spacer></v-spacer>
    <span class="grey--text">{{j.time}}</span><br>
  </v-card-title>

  <v-card-actions>
    <span v-html="j.highlight">
    </span>
  </v-card-actions>
</v-card>
</div>

<div class="text-xs-center hit" v-if="tot_page > 0">
<v-pagination v-model="cur_page" :length="tot_page">
</v-pagination>
</div>

<v-footer>
  <v-spacer></v-spacer>
  <img src="favicon.ico"/>
  &nbsp; vov-vov!
  <v-spacer></v-spacer>
  <!-- {{cur_page}}/{{tot_page}} -->
</v-footer>

</v-app>
</template>

<script>
import axios from 'axios' /* AJAX request lib */

export default {
  watch: {
    "cur_page": function (newPage, oldPage) {
      this.cur_page = newPage
      this.tot_page = 0
      this.list = []
      if (newPage > 0)
        this.on_search(newPage)
      { /* scroll to top */
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0;
      }
    }
  },
  methods: {
    on_search(page) {
      const qry = this.qry
      var vm = this
      this.fired = true
      this.firing = true
      axios.get('query', {
          params: {
          'q': qry, 'p': page
        }
      }).then(function (res) {
        vm.cur_page = res.data.cur_page
        vm.tot_page = res.data.tot_page
        vm.list = res.data.list
        vm.firing = false
      })
    },
    openlink(link) {
      var fields = link.split('/')
      const idx = fields.indexOf('master-tree')
      fields = fields.slice(idx + 1, fields.length)
      return '/droppy/#/' + fields.join('/')
    }
  },
  data: function () {
    return {
      "firing": false,
      "fired": false,
      "qry": "",
      "cur_page": 1,
      "tot_page": 0,
      "list": []
    }
  }
}
</script>
<style>
.hit {
  padding-top: 10px;
  padding-bottom: 10px;
  background-color: #b99a83;
}
</style>
