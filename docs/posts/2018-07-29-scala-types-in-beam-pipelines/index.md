---
title: Scala Types in Scio Pipelines
date: 2018-07-29
category: Data Engineering
tags:
 - scala
 - apache-beam
 - scio
description: For very little effort, Scala's Type Aliases can help you keep track of what means what in your Scio Beam pipelines.
---

Data pipelines in [Apache Beam](https://beam.apache.org/) have a distinctly functional flavour, whichever language you use. That's because they can be distributed over a cluster of machines, so careful management of state and side-effects is important.

[Spotify's Scio](https://github.com/spotify/scio) is an excellent Scala API for Beam.
Scala's functional ideas help to cut out much of the boilerplate present in the native Java API.

Scio makes good use of Scala's tuple types, in particular pairs `(x, y)`.
Its [PairSCollectionFunctions](https://spotify.github.io/scio/api/com/spotify/scio/values/PairSCollectionFunctions.html)
add some neat, expressive functionality to the standard [SCollection](https://spotify.github.io/scio/api/com/spotify/scio/values/SCollection.html)
to compute values based on pairs.

That capability lets you write really concise code, but can make it hard to make sense of types in the middle of your pipeline.
Using Scala's `type` keyword to alias common types can bring more clarity to your code.

## An Example: Counting in Access Logs

At this point, I think I need an example.
Let's say we're processing simple web server access logs.
I want to know how many times each user accesses each URL and the status code they received.

Here's an example of a line from our logs:

    1.2.3.4,bob,2017-01-01T00:00:00.001Z,/,200

We don't need to worry too much about where the logs are coming from.
Aside from this just being an example,
Beam has numerous adapters for different data sources.

I first write a case class and a parse function to turn these useless strings of characters into something nicer to work with.

```scala
object AccessLog {

  case class Entry(clientIp: String, userId: String, timestamp: Instant, path: String, statusCode: Int)

  def parseLine(line: String): Entry = line.split(",") match {
    case Array(clientIp, userId, timestamp, path, statusCode) =>
      Entry(clientIp, userId, new Instant(timestamp), path, statusCode.toInt)
  }
}
```

Now, we can build a pipeline starting with this parse function.
We'll build up the pipeline step by step, detailing the type signature at each point.
The type at the end of the pipeline will be indicated with a comment on the next line.

```scala
sc.textFile(args("input"))
  .map(AccessLog.parseLine)

// SCollection[AccessLog.Entry]
```

So far so good. Now, let's map `AccessLog.Entry` onto the key we want to group by.

```scala
sc.textFile(args("input"))
  .map(AccessLog.parseLine)
  .map(x => (x.userId, x.path, x.statusCode))

// SCollection[(String, String, Int)]
```

Yuk. Now we need to remember that the first `String` is the userId, the second is the path and the final `Int` is the statusCode.
It gets worse when we start aggregating, adding more complexity and numbers into the mix.

```scala
sc.textFile(args("input"))
  .map(AccessLog.parseLine)
  .map(x => (x.userId, x.path, x.statusCode))
  .countByValue

// SCollection[((String, String, Int), Long)]
```

This is a very simple pipeline.
When you've got something more complex it gets harder to keep track of what these types mean,
and when you are working with more than one pipeline it's harder still.
The type system can help more than it is, so let's use it.

## Once More, With Type Aliases

OK, so let's back up, and use Scala's `type` keyword to make the type signatures a bit more useful.
Our parsing function is a convenient place to introduce additional type information to flow through the pipeline.

```scala
type ClientIp = String
type UserId = String
type Path = String
type StatusCode = Int
case class Entry(clientIp: ClientIp, userId: UserId, timestamp: Instant, path: Path, statusCode: StatusCode)
```

That's it.
Everything still type-checks, as the "real" types haven't changed.
Our new aliases will now flow through the pipeline code,
allowing us to see what the types really meant at each point.
Let's retrace our steps and see how these new types help us out.
This time, I'll comment the types at each step for brevity.

```scala
sc.textFile(args("input"))
  .map(AccessLog.parseLine)
  // SCollection[AccessLog.Entry]
  .map(x => (x.userId, x.path, x.statusCode))
  // SCollection[(UserId, Path, StatusCode)]
  .countByValue
  // SCollection[((UserId, Path, StatusCode), Long)]
```

An IDE like IntelliJ (keyboard shortcut Alt-=, probably something slightly different on a Mac) will tell you what the values you're dealing with as you code.
The type alias syntax is concise too, much better than having to create classes.
It's not a lot of extra thinking or typing for a significant increase in the amount of information you have as you're writing
or debugging a pipeline.
The custom parse function early in the pipeline provides a neat starting point to inject this type information
and have it flow through the rest of our pipeline.

Source code for this example can be found at https://github.com/brabster/beam-scala-types-example
