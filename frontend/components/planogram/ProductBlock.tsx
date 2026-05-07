"use client";

import { useMemo } from "react";
import { Group, Rect, Text } from "react-konva";
import type Konva from "konva";

import type { PlanogramProduct } from "@/types/planogram";

interface ProductBlockProps {
  product: PlanogramProduct;
  xPx: number;
  yPx: number;
  widthPx: number;
  heightPx: number;
  isSelected: boolean;
  onSelect: () => void;
  onDragEnd: (event: Konva.KonvaEventObject<DragEvent>) => void;
}

const isDark = (hex: string): boolean => {
  const cleaned = (hex || "").replace("#", "");
  if (cleaned.length !== 6) return false;
  const r = parseInt(cleaned.slice(0, 2), 16);
  const g = parseInt(cleaned.slice(2, 4), 16);
  const b = parseInt(cleaned.slice(4, 6), 16);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b < 140;
};

export default function ProductBlock({
  product,
  xPx,
  yPx,
  widthPx,
  heightPx,
  isSelected,
  onSelect,
  onDragEnd,
}: ProductBlockProps) {
  const textColor = useMemo(
    () => (isDark(product.color_hex) ? "#FFFFFF" : "#11201B"),
    [product.color_hex],
  );

  return (
    <Group x={xPx} y={yPx} draggable onClick={onSelect} onTap={onSelect} onDragEnd={onDragEnd}>
      <Rect
        width={widthPx}
        height={heightPx}
        fill={product.color_hex}
        stroke={isSelected ? "#185f4d" : "#11201B"}
        strokeWidth={isSelected ? 3 : 1}
        cornerRadius={3}
        shadowEnabled={isSelected}
        shadowColor="#185f4d"
        shadowBlur={isSelected ? 6 : 0}
        shadowOpacity={0.4}
      />
      <Text
        x={6}
        y={6}
        text={product.sku}
        fontSize={11}
        fontStyle="bold"
        fill={textColor}
        width={Math.max(20, widthPx - 12)}
        ellipsis
        wrap="none"
      />
      <Text
        x={6}
        y={22}
        text={product.name}
        fontSize={9}
        fill={textColor}
        width={Math.max(20, widthPx - 12)}
        ellipsis
        wrap="none"
      />
      {product.facing_count > 1 ? (
        <Text
          x={Math.max(0, widthPx - 24)}
          y={Math.max(0, heightPx - 14)}
          text={`x${product.facing_count}`}
          fontSize={9}
          fontStyle="italic"
          fill={textColor}
          align="right"
          width={20}
        />
      ) : null}
    </Group>
  );
}
