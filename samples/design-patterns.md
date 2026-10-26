# Software Design: Design Patterns

## Strategy
The Strategy pattern defines a family of algorithms behind a common interface.
A context delegates an operation to a selected strategy. A strategy can change at
runtime without changing the context. For example, a learning service can select
a flashcard generation strategy or a quiz generation strategy.

## Observer
The Observer pattern lets a subject notify subscribed observers when an event
occurs. Publishers do not need to know the concrete observers. For example, a
completed quiz can publish an AttemptRecorded event. A progress projector observes
that event and updates mastery statistics.

## Adapter
The Adapter pattern translates an existing interface into the interface a client
expects. An OpenAI adapter converts a provider-neutral generation request into an
HTTP request and converts the response back into a domain result.

## State
The State pattern represents state-specific behavior in separate objects. A
context delegates legal transitions to its current state. A paused study session
can resume, while a completed session cannot resume. This prevents inconsistent
combinations of boolean flags.

## Command
The Command pattern encapsulates a request as an object. An invoker executes the
command, which delegates to a receiver. Both a graphical interface and a command
line can submit the same command without duplicating the operation's rules.

## Facade and MVC
A Facade provides a simple entry point to a group of collaborating subsystems.
Model View Controller separates presentation, request coordination, and application
data. Together they keep a graphical interface and a command line consistent.
