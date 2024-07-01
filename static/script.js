function fetchProductData(asin) {
    var url = '/compare/' + encodeURIComponent(asin);
    window.location.href = url;
}