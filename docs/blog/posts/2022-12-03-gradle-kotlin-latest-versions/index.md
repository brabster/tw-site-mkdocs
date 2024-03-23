---
title: Latest Stable Versions with Kotlin and Gradle
date: 2022-12-03
category: DevOps
draft: true
tags:
 - gotcha
 - gradle
 - security
 - kotlin
 - dependencies
---

> How do you update all your Kotlin dependencies to the latest stable versions?

This question isn't as straightforward to answer as you might expect, as a team-mate and I discovered.
We were able to piece together an approach that just about works, but Gradle support for Kotlin itself presents a challenge we were unable to solve.
To explain, let's set up a simple Kotlin Gradle project to illustrate the goal and solution steps.

## The Example Project

I've got Gradle 7.2 installed - it's the current version [officially available as a Ubuntu snap](https://snapcraft.io/install/gradle/ubuntu). More on that shortly.

```console
$ gradle --version

------------------------------------------------------------
Gradle 7.2
------------------------------------------------------------

Build time:   2021-08-17 09:59:03 UTC
Revision:     a773786b58bb28710e3dc96c4d1a7063628952ad

Kotlin:       1.5.21
Groovy:       3.0.8
Ant:          Apache Ant(TM) version 1.10.9 compiled on September 27 2020
JVM:          16.0.1 (Private Build 16.0.1+9-Ubuntu-120.04)
OS:           Linux 5.15.0-53-generic amd64
```

Init-ing a minimal Kotlin application:

```console
$ gradle init --type kotlin-application

Select build script DSL:
  1: Groovy
  2: Kotlin
Enter selection (default: Kotlin) [1..2] 1

Project name (default: gradle-dependency-update-example): 
Source package (default: gradle.dependency.update.example): app
```

Our minimal project now has one configuration file that we'll be working with, `app/build.gradle`.
The initial content of the interesting sections - plugins and dependencies - follows.

```groovy
plugins {
    // Apply the org.jetbrains.kotlin.jvm Plugin to add support for Kotlin.
    id 'org.jetbrains.kotlin.jvm' version '1.5.0'

    // Apply the application plugin to add support for building a CLI application in Java.
    id 'application'
}

dependencies {
    // Align versions of all Kotlin components
    implementation platform('org.jetbrains.kotlin:kotlin-bom')

    // Use the Kotlin JDK 8 standard library.
    implementation 'org.jetbrains.kotlin:kotlin-stdlib-jdk8'

    // This dependency is used by the application.
    implementation 'com.google.guava:guava:30.1.1-jre'

    // Use the Kotlin test library.
    testImplementation 'org.jetbrains.kotlin:kotlin-test'

    // Use the Kotlin JUnit integration.
    testImplementation 'org.jetbrains.kotlin:kotlin-test-junit'
}
```

{{< img src="latest-stable-meme.jpg" alt="Meme. Anakin: I inited a new Kotlin project in Gradle. Padme: So it's got the latest versions of everything, right? Right?" >}}
(credit to https://imgflip.com/)

Do we have the latest versions of these default dependencies? How would we know?

## Gradle's Built-In Tooling

Gradle's built-in [dependency management tooling](https://docs.gradle.org/current/userguide/viewing_debugging_dependencies.html) might be helpful. Let's try see what we can do.

```console
$ ./gradlew app:dependencies|wc -l
317
```

317 lines of output to describe the dependency graph! Let's narrow it down a little. What's on the compilation classpath?

```console
$ ./gradlew app:dependencies --configuration compileClasspath

> Task :app:dependencies

------------------------------------------------------------
Project ':app'
------------------------------------------------------------

compileClasspath - Compile classpath for compilation 'main' (target  (jvm)).
+--- org.jetbrains.kotlin:kotlin-bom:1.5.0
|    +--- org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.5.0 (c)
|    +--- org.jetbrains.kotlin:kotlin-stdlib:1.5.0 (c)
|    +--- org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.5.0 (c)
|    \--- org.jetbrains.kotlin:kotlin-stdlib-common:1.5.0 (c)
+--- org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.5.0
|    +--- org.jetbrains.kotlin:kotlin-stdlib:1.5.0
|    |    +--- org.jetbrains:annotations:13.0
|    |    \--- org.jetbrains.kotlin:kotlin-stdlib-common:1.5.0
|    \--- org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.5.0
|         \--- org.jetbrains.kotlin:kotlin-stdlib:1.5.0 (*)
\--- com.google.guava:guava:30.1.1-jre
     +--- com.google.guava:failureaccess:1.0.1
     +--- com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
     +--- com.google.code.findbugs:jsr305:3.0.2
     +--- org.checkerframework:checker-qual:3.8.0
     +--- com.google.errorprone:error_prone_annotations:2.5.1
     \--- com.google.j2objc:j2objc-annotations:1.3

(c) - dependency constraint
(*) - dependencies omitted (listed previously)

A web-based, searchable dependency report is available by adding the --scan option.
```

OK, so I see the direct and transitive dependencies that are being resolved, but no information about how up to date we are.
Maybe that `--scan` option will help? Same output, but now...

```console
Publishing a build scan to scans.gradle.com requires accepting the Gradle Terms of Service defined at https://gradle.com/terms-of-service. Do you accept these terms? [yes, no]
```

Hmmm. That's a bit of showstopper in the real world. We can't just go uploading stuff to third party services. I'm curious what we'd see though, so I'm going to accept for this example project.

```console
Gradle Terms of Service accepted.

Publishing build scan...
https://gradle.com/s/m5lvgkdeb4pyy
```
I click the link, give my email address in the form that follows, wait for the email and then I get a link to the scan, which I can share with you, if you're interested. The scan is [here](https://scans.gradle.com/s/m5lvgkdeb4pyy). I can't see anything in there to help me understand whether I'm up to date or not.

The `dependencyInsight` task doesn't help either. All these built-in tools are for understanding why a specific version of a dependency was chosen by the dependency resolution mechanism. There's nothing built-in to help me understand whether I'm up to date.

## Plugin [`gradle-versions-plugin`](https://github.com/ben-manes/gradle-versions-plugin)

Shout out to the awesome, third-party [`gradle-versions-plugin`](https://github.com/ben-manes/gradle-versions-plugin).
Let's configure it up and see what it tells us.

```groovy
plugins {
    // Apply the org.jetbrains.kotlin.jvm Plugin to add support for Kotlin.
    id 'org.jetbrains.kotlin.jvm' version '1.5.0'

    // Apply the application plugin to add support for building a CLI application in Java.
    id 'application'

    // Manually added to check for updates
    id "com.github.ben-manes.versions" version '0.43.0'
}
```

Running the new task:

```console
$ ./gradlew dependencyUpdates

> Task :app:dependencyUpdates

------------------------------------------------------------
:app Project Dependency Updates (report to plain text file)
------------------------------------------------------------

The following dependencies have later milestone versions:
 - com.github.ben-manes.versions:com.github.ben-manes.versions.gradle.plugin [0.43.0 -> 0.44.0]
 - com.google.guava:guava [30.1.1-jre -> 31.1-jre]
     https://github.com/google/guava
 - org.jetbrains.kotlin:kotlin-bom [1.5.0 -> 1.8.0-Beta]
     https://kotlinlang.org/
 - org.jetbrains.kotlin:kotlin-scripting-compiler-embeddable [1.5.0 -> 1.8.0-Beta]
     https://kotlinlang.org/
 - org.jetbrains.kotlin:kotlin-stdlib-jdk8 [1.5.0 -> 1.8.0-Beta]
     https://kotlinlang.org/
 - org.jetbrains.kotlin:kotlin-test-junit [1.5.0 -> 1.8.0-Beta]
     https://kotlinlang.org/
 - org.jetbrains.kotlin.jvm:org.jetbrains.kotlin.jvm.gradle.plugin [1.5.0 -> 1.8.0-Beta]
     https://kotlinlang.org/

Failed to determine the latest version for the following dependencies (use --info for details):
 - org.jetbrains.kotlin:kotlin-test
     1.8.0-Beta

Gradle release-candidate updates:
 - Gradle: [7.2 -> 7.6]

Generated report file build/dependencyUpdates/report.txt
```

Wow! Now we're getting somewhere. It tells me that there's everything in there has a newer version available, including the Gradle wrapper and the versions plugin itself. It also tells me that there's a much newer version of Kotlin itself available - `1.8.0-Beta`. This is where the "stable" part of the post's title comes in. I might not want versions that declare themselves to be "unstable" in important applications that someone is depending on.

The gradle-versions-plugin describes an approach to solve this problem. It turns out that Gradle allows you to hook into the dependency resolution process and influence what's considered acceptable. 

```groovy
def isNonStable = { String version ->
  def stableKeyword = ['RELEASE', 'FINAL', 'GA'].any { it -> version.toUpperCase().contains(it) }
  def regex = /^[0-9,.v-]+(-r)?$/
  return !stableKeyword && !(version ==~ regex)
}

configurations.all {
  resolutionStrategy {
    componentSelection {
      all {
        if (isNonStable(it.candidate.version) && !isNonStable(it.currentVersion)) {
          reject('not a stable version')
        }
      }
    }
  }
}
```

First, we define an `isNonStable` function. This function says that a candidate version string is considered stable if
- it mentions 'release', 'final' or 'ga' (case-insensitive)
- or if it matches a regex
- it is `nonStable` by those rules, but so is the current version

Let's try our `dependencyUpdates` task again.

```console
$ ./gradlew dependencyUpdates

> Task :app:dependencyUpdates

------------------------------------------------------------
:app Project Dependency Updates (report to plain text file)
------------------------------------------------------------

The following dependencies have later milestone versions:
 - com.github.ben-manes.versions:com.github.ben-manes.versions.gradle.plugin [0.43.0 -> 0.44.0]
 - org.jetbrains.kotlin.jvm:org.jetbrains.kotlin.jvm.gradle.plugin [1.5.0 -> 1.8.0-Beta]
     https://kotlinlang.org/

Failed to determine the latest version for the following dependencies (use --info for details):
 - org.jetbrains.kotlin:kotlin-scripting-compiler-embeddable

Gradle release-candidate updates:
 - Gradle: [7.2 -> 7.6]
 ```

 Huh? Why are we still seeing `1.8.0-Beta` for the latest stable version of the Gradle plugin? Why were we unable to determine the latest version for the `kotlin-scripting-compiler-embeddable`? Using the `--info` flag as suggested...

 ```console
 Caused by: groovy.lang.MissingPropertyException: No such property: currentVersion for class: org.gradle.api.internal.artifacts.DefaultComponentSelection
 ```

 ...we can see that there's a problem ascertaining the `currentVersion` for some of the dependencies. 
