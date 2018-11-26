import "todomvc-common/base.css";
import "todomvc-app-css/index.css";

import "todomvc-common/base.js";
import "director";

import Vue from 'vue';
import Popup from './popup/Popup.vue';

new Vue({
  el: '#app',
  render: c => c(Popup)
});
