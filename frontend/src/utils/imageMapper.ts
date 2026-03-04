import { StaticImageData } from "next/image";

import queenAnne from "@/assets/images/1425-queen-anne-ave-n.png";
import capitolHill from "@/assets/images/1890-capitol-hill-blvd.png";
import beaconAve from "@/assets/images/2301-beacon-ave-s.png";
import pacificSt from "@/assets/images/2847-ne-pacific-st.png";
import fremontAve from "@/assets/images/3421-fremont-ave-n.png";
import rainierAve from "@/assets/images/3812-rainier-ave-s.png";
import alaskaSt from "@/assets/images/4021-alaska-st-sw.png";
import ballardAve from "@/assets/images/5012-ballard-ave-nw.png";
import aveNe from "@/assets/images/5512-20th-ave-ne.png";
import greenwoodAve from "@/assets/images/6140-greenwood-ave-n.png";
import austinTx from "@/assets/images/austin-tx.png";
import denverCo from "@/assets/images/denver-co.png";
import nashvilleTn from "@/assets/images/nashville-tn.png";
import portlandOr from "@/assets/images/portland-or.png";
import seattleWa from "@/assets/images/seattle-wa.png";

export const imageMap: Record<string, StaticImageData> = {
    "1425-queen-anne-ave-n.png": queenAnne,
    "1890-capitol-hill-blvd.png": capitolHill,
    "2301-beacon-ave-s.png": beaconAve,
    "2847-ne-pacific-st.png": pacificSt,
    "3421-fremont-ave-n.png": fremontAve,
    "3812-rainier-ave-s.png": rainierAve,
    "4021-alaska-st-sw.png": alaskaSt,
    "5012-ballard-ave-nw.png": ballardAve,
    "5512-20th-ave-ne.png": aveNe,
    "6140-greenwood-ave-n.png": greenwoodAve,
    "austin-tx.png": austinTx,
    "denver-co.png": denverCo,
    "nashville-tn.png": nashvilleTn,
    "portland-or.png": portlandOr,
    "seattle-wa.png": seattleWa,
};
