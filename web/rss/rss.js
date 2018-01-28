const items = pegasus(config.storiesURL);

const app = new Vue({ // eslint-disable-line no-unused-vars
  el: '#app',
  data: {
    items: [],
    updated: null,
  },

  mounted: function mounted() {
    items.then((data) => {
      const items = data.items.map((item) => {
        let short = item.summary.substr(0, 400);
        const dt = moment(item.date);

        if (item.summary.length > 500) {
          short = short.substr(0, Math.min(short.length, short.lastIndexOf(' '))) + ' ...';
        }
        const obj = Object.assign({
          dateStr: dt.format('MMM DD h:mma'),
          ts: parseInt(dt.format('X')),
          shortSummary: short,
        }, item);
        console.log(obj);
        return obj;
      });
      this.items = _.sortBy(items, ['ts']);
      this.updated = moment(data.updated);
    });
  },

  computed: {
    updatedStr: function updatedStr() {
      return this.updated ? this.updated.format('dddd, MMMM D, h:mm a') : '';
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
