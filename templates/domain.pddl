(define (domain delivery)
  (:requirements :strips :typing)
  
  (:types
    robot - object
    room - object
  )
  
  (:predicates
    (at ?r - robot ?room - room)
    (connected ?room1 - room ?room2 - room)
  )
  
  (:action move
    :parameters (?r - robot ?from - room ?to - room)
    :precondition (and 
      (at ?r ?from)
      (connected ?from ?to)
    )
    :effect (and 
      (not (at ?r ?from))
      (at ?r ?to)
    )
  )
)