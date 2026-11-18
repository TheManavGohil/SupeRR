# Player portrait inventory

All twenty supplied images were visually inspected on 18 November 2026. Files are preserved under `public/player_image/`; the UI uses the reviewed manifest at `content/player-assets.json`. Names follow the supplied filenames and frozen player IDs. This is not independent verification of the generated facial likenesses.

| List / rank | Player               | Source filename | Pixels      | File size |
| ----------- | -------------------- | --------------- | ----------- | --------- |
| Batting 1   | Tim David            | Tim.png         | 641 × 800   | 726 KiB   |
| Batting 2   | Suryakumar Yadav     | Suryakumar.png  | 633 × 800   | 732 KiB   |
| Batting 3   | Nicholas Pooran      | Nicholas.png    | 633 × 800   | 721 KiB   |
| Batting 4   | Shashank Singh       | Shashank.png    | 327 × 407   | 189 KiB   |
| Batting 5   | Jacob Bethell        | Jacob.png       | 327 × 407   | 182 KiB   |
| Batting 6   | Andre Russell        | Andre.png       | 327 × 393   | 187 KiB   |
| Batting 7   | Romario Shepherd     | Romario.png     | 327 × 393   | 182 KiB   |
| Batting 8   | Namboori Tilak Varma | Namboori.png    | 329 × 769   | 390 KiB   |
| Batting 9   | Shreyas Iyer         | Shreyas.png     | 322 × 769   | 358 KiB   |
| Batting 10  | Liam Livingstone     | Liam.png        | 329 × 769   | 368 KiB   |
| Bowling 1   | Sunil Narine         | sunil.png       | 329 × 769   | 371 KiB   |
| Bowling 2   | Jasprit Bumrah       | jasprit.png     | 341 × 769   | 402 KiB   |
| Bowling 3   | Mustafizur Rahman    | Mustafizur.png  | 313 × 769   | 361 KiB   |
| Bowling 4   | Mahedi Hasan         | mahedi.png      | 630 × 801   | 685 KiB   |
| Bowling 5   | Spencer Johnson      | Spencer.png     | 630 × 801   | 701 KiB   |
| Bowling 6   | Sakib Hussain        | Sakib.png       | 630 × 801   | 616 KiB   |
| Bowling 7   | Varun Chakravarthy   | varun.png       | 630 × 801   | 621 KiB   |
| Bowling 8   | Rasikh Salam         | Rasikh.png      | 630 × 801   | 606 KiB   |
| Bowling 9   | Anukul Roy           | Anukul.png      | 630 × 801   | 619 KiB   |
| Bowling 10  | Piyush Chawla        | piyush.png      | 1122 × 1402 | 2100 KiB  |

The source files total 11,384,451 bytes (10.86 MiB). Width-to-height ratios range from 0.407 to 0.832. Several originals are only 313–341 pixels wide; their detail is limited by that source resolution.

The display uses a consistent 4:5 viewport with individual framing. Tall screenshots retain a head-and-torso crop with white padding at the sides. Tighter portraits retain their existing closer composition. Thin screenshot rules, the top pink strips on the Russell/Shepherd images and neighbouring-jersey slivers on several tall screenshots are hidden with explicit edge trims. Faces and jerseys are not regenerated or retouched. No destructive crop is saved over an original.

The crop viewport is expressed in original-image pixels. Its width is always 0.8 × its height, and the source image scales proportionally within it. Cards and profiles use that aspect ratio; the homepage centres the same viewport inside its responsive feature panel. Original rank labels sit in small, bordered badges rather than across the player's body. Alternative profiles without a supplied portrait retain the existing placeholder.

`next/image` supplies responsive AVIF/WebP delivery. Large PNGs are not loaded directly into the gallery; the source files remain available for replacements. Review the network payload again if the images or image-quality settings change.
