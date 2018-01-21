const items = pegasus(config.storiesURL);

const app = new Vue({ // eslint-disable-line no-unused-vars
  el: '#app',
  data: {
    items: [],
    updated: null,
  },

  mounted: function mounted() {
    items.then((data) => {
      this.items = data.items.map(item => Object.assign({ dateStr: moment(item.date).format('MMM DD h:mma') }, item));
      this.updated = moment(data.updated);
    });
  },

  computed: {
    updatedStr: function updatedStr() {
      return this.updated ? this.updated.format('dddd, MMMM D, h:mm:ss a') : '';
    },
  },

  methods: {
    read: function(ev) {
      // on click href, post url and title to webhook
      const body = {
        value1: ev.target.href,
        balue2: $(ev.target).text(),
      };

      $.post(config.webhookURL, body);
    },
  },
});
