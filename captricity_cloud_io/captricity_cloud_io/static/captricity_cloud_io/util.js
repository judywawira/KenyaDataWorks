/* Based on David Koelle's alphanum sorting algorithm
 * http://www.davekoelle.com/alphanum.html
 */
naturalStringCompare = function (str1, str2) {
    var strChunks1 = str1.toLowerCase().split(/(\d+)|[-_\.\/]/g);
    var strChunks2 = str2.toLowerCase().split(/(\d+)|[-_\.\/]/g);
  
    for (x = 0; x < Math.max(strChunks1.length, strChunks2.length); x++) {
        if (strChunks1[x] !== strChunks2[x]) {
            var a = Number(strChunks1[x]), b = Number(strChunks2[x]);
            if (a == strChunks1[x] && b == strChunks2[x]) {
                return a - b;
            } else return (strChunks1[x] > strChunks2[x]) ? 1 : -1;
        }
    }
    return strChunks1.length - strChunks2.length;
}
