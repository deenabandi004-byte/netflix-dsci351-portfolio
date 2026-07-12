// DSCI 351 — Netflix Analysis, Part 2.1 MongoDB Queries
//
// Load the Netflix table exported from MySQL into a `movies` collection and
// the raw netflix titles catalog into a `netflix_titles` collection. Then run
// these aggregations from mongosh or MongoDB Compass.
//
// Example load (mongosh):
//   mongoimport --db netflix --collection movies         --type csv --headerline --file movies.csv
//   mongoimport --db netflix --collection netflix_titles --type csv --headerline --file netflix_titles.csv


// Q1. Newest 5 movies by release year.
db.movies.aggregate([
  { $match: { type: "Movie" } },
  { $sort: { release_year: -1 } },
  { $project: { _id: 0, title: 1, release_year: 1 } },
  { $limit: 5 }
]);


// Q2. Count movies per MPAA/TV rating (sorted high to low).
db.movies.aggregate([
  { $match: { type: "Movie" } },
  { $group: { _id: "$rating", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
]);


// Q3. Average release year per rating.
db.movies.aggregate([
  { $match: { type: "Movie", release_year: { $ne: null } } },
  { $group: { _id: "$rating", avg_release_year: { $avg: "$release_year" } } },
  { $sort: { _id: 1 } }
]);


// Q4. Ratings with more than 3 titles.
db.movies.aggregate([
  { $match: { type: "Movie" } },
  { $group: { _id: "$rating", count: { $sum: 1 } } },
  { $match: { count: { $gt: 3 } } },
  { $sort: { _id: 1 } }
]);


// Q5. Uppercase titles, first 10.
db.movies.aggregate([
  { $match: { type: "Movie" } },
  { $project: { _id: 0, title_upper: { $toUpper: "$title" } } },
  { $limit: 10 }
]);


// Q6. Directors with more than one title.
db.movies.aggregate([
  { $match: { type: "Movie", director: { $ne: null } } },
  { $group: { _id: "$director", movie_count: { $sum: 1 } } },
  { $match: { movie_count: { $gt: 1 } } },
  { $sort: { movie_count: -1 } }
]);


// Q7. Titles whose description mentions "father" (case-insensitive).
db.movies.aggregate([
  { $match: { type: "Movie", description: { $regex: "father", $options: "i" } } },
  { $project: { _id: 0, title: 1, description: 1 } },
  { $limit: 10 }
]);


// Q8. Titles that appear in both collections with year > 1995 (uses $lookup).
db.movies.aggregate([
  { $match: { release_year: { $gt: 1995 } } },
  {
    $lookup: {
      from: "netflix_titles",
      let: { t: "$title", y: "$release_year" },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$title", "$$t"] },
                { $eq: ["$release_year", "$$y"] }
              ]
            }
          }
        }
      ],
      as: "match_in_netflix_titles"
    }
  },
  { $match: { match_in_netflix_titles: { $ne: [] } } },
  { $project: { _id: 0, title: 1, release_year: 1 } },
  { $sort: { release_year: 1, title: 1 } }
]);
