'use client';

import { useState, useEffect, useRef } from 'react';

const GRID_SIZE = 20;
const CELL_SIZE = 20;
const INITIAL_SPEED = 100;

type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT';
type Segment = { x: number; y: number };

export default function SnakeGame() {
  const [snake, setSnake] = useState<Segment[]>([{ x: 10, y: 10 }]);
  const [food, setFood] = useState<Segment>({ x: 15, y: 15 });
  const [direction, setDirection] = useState<Direction>('RIGHT');
  const [nextDirection, setNextDirection] = useState<Direction>('RIGHT');
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const gameLoopRef = useRef<NodeJS.Timeout | null>(null);

  // Generate random food position
  const generateFood = (): Segment => {
    let newFood: Segment;
    do {
      newFood = {
        x: Math.floor(Math.random() * GRID_SIZE),
        y: Math.floor(Math.random() * GRID_SIZE),
      };
    } while (snake.some((seg) => seg.x === newFood.x && seg.y === newFood.y));
    return newFood;
  };

  // Game loop
  useEffect(() => {
    if (gameOver) return;

    gameLoopRef.current = setInterval(() => {
      setSnake((prevSnake) => {
        setDirection(nextDirection);
        const head = prevSnake[0];
        let newHead = { ...head };

        switch (nextDirection) {
          case 'UP':
            newHead.y = (head.y - 1 + GRID_SIZE) % GRID_SIZE;
            break;
          case 'DOWN':
            newHead.y = (head.y + 1) % GRID_SIZE;
            break;
          case 'LEFT':
            newHead.x = (head.x - 1 + GRID_SIZE) % GRID_SIZE;
            break;
          case 'RIGHT':
            newHead.x = (head.x + 1) % GRID_SIZE;
            break;
        }

        // Check collision with self
        if (prevSnake.some((seg) => seg.x === newHead.x && seg.y === newHead.y)) {
          setGameOver(true);
          return prevSnake;
        }

        let newSnake = [newHead, ...prevSnake];

        // Check if food eaten
        if (newHead.x === food.x && newHead.y === food.y) {
          setScore((prev) => prev + 10);
          setFood(generateFood());
        } else {
          newSnake.pop();
        }

        return newSnake;
      });
    }, INITIAL_SPEED);

    return () => {
      if (gameLoopRef.current) clearInterval(gameLoopRef.current);
    };
  }, [gameOver, food, nextDirection, snake]);

  // Handle keyboard input
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowUp':
          if (direction !== 'DOWN') setNextDirection('UP');
          e.preventDefault();
          break;
        case 'ArrowDown':
          if (direction !== 'UP') setNextDirection('DOWN');
          e.preventDefault();
          break;
        case 'ArrowLeft':
          if (direction !== 'RIGHT') setNextDirection('LEFT');
          e.preventDefault();
          break;
        case 'ArrowRight':
          if (direction !== 'LEFT') setNextDirection('RIGHT');
          e.preventDefault();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [direction]);

  const resetGame = () => {
    setSnake([{ x: 10, y: 10 }]);
    setFood({ x: 15, y: 15 });
    setDirection('RIGHT');
    setNextDirection('RIGHT');
    setGameOver(false);
    setScore(0);
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-6 bg-white rounded-lg shadow-lg">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-padma-red">Snake Game</h2>
        <p className="text-xs text-gray-500 mt-1">Use arrow keys</p>
      </div>

      <div className="relative bg-gray-900 border-4 border-padma-red rounded-lg overflow-hidden">
        <div
          style={{
            width: GRID_SIZE * CELL_SIZE,
            height: GRID_SIZE * CELL_SIZE,
            display: 'grid',
            gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`,
            gap: 0,
          }}
        >
          {Array.from({ length: GRID_SIZE * GRID_SIZE }).map((_, idx) => {
            const x = idx % GRID_SIZE;
            const y = Math.floor(idx / GRID_SIZE);
            const isSnake = snake.some((seg) => seg.x === x && seg.y === y);
            const isFood = food.x === x && food.y === y;
            const isHead = snake[0].x === x && snake[0].y === y;

            return (
              <div
                key={idx}
                className={`${
                  isSnake
                    ? isHead
                      ? 'bg-padma-red'
                      : 'bg-padma-blue'
                    : isFood
                    ? 'bg-yellow-400'
                    : 'bg-gray-800'
                } border border-gray-700`}
                style={{
                  width: CELL_SIZE,
                  height: CELL_SIZE,
                }}
              />
            );
          })}
        </div>
      </div>

      <div className="text-center">
        <p className="text-lg font-bold text-padma-blue">Score: {score}</p>
        {gameOver && (
          <div className="mt-4">
            <p className="text-red-600 font-bold mb-2">Game Over!</p>
            <button
              onClick={resetGame}
              className="px-6 py-2 bg-padma-red text-white rounded-lg font-bold hover:shadow-lg transition-all duration-300 transform hover:scale-105"
            >
              Play Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
