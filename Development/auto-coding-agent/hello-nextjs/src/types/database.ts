/**
 * Database types for Supabase.
 * These types are generated from the database schema.
 * Run `npx supabase gen types typescript --project-id your-project-id > src/types/database.ts` to regenerate.
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      projects: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          story: string | null;
          style: string | null;
          stage: project_stage;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          title: string;
          story?: string | null;
          style?: string | null;
          stage?: project_stage;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          title?: string;
          story?: string | null;
          style?: string | null;
          stage?: project_stage;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "projects_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
        ];
      };
      scenes: {
        Row: {
          id: string;
          project_id: string;
          order_index: number;
          description: string;
          description_confirmed: boolean;
          image_status: image_status;
          image_confirmed: boolean;
          video_status: video_status;
          video_confirmed: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          project_id: string;
          order_index: number;
          description: string;
          description_confirmed?: boolean;
          image_status?: image_status;
          image_confirmed?: boolean;
          video_status?: video_status;
          video_confirmed?: boolean;
          created_at?: string;
        };
        Update: {
          id?: string;
          project_id?: string;
          order_index?: number;
          description?: string;
          description_confirmed?: boolean;
          image_status?: image_status;
          image_confirmed?: boolean;
          video_status?: video_status;
          video_confirmed?: boolean;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "scenes_project_id_fkey";
            columns: ["project_id"];
            isOneToOne: false;
            referencedRelation: "projects";
            referencedColumns: ["id"];
          },
        ];
      };
      images: {
        Row: {
          id: string;
          scene_id: string;
          storage_path: string;
          url: string;
          width: number | null;
          height: number | null;
          version: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          scene_id: string;
          storage_path: string;
          url: string;
          width?: number | null;
          height?: number | null;
          version?: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          scene_id?: string;
          storage_path?: string;
          url?: string;
          width?: number | null;
          height?: number | null;
          version?: number;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "images_scene_id_fkey";
            columns: ["scene_id"];
            isOneToOne: false;
            referencedRelation: "scenes";
            referencedColumns: ["id"];
          },
        ];
      };
      videos: {
        Row: {
          id: string;
          scene_id: string;
          storage_path: string;
          url: string;
          duration: number | null;
          task_id: string | null;
          version: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          scene_id: string;
          storage_path: string;
          url: string;
          duration?: number | null;
          task_id?: string | null;
          version?: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          scene_id?: string;
          storage_path?: string;
          url?: string;
          duration?: number | null;
          task_id?: string | null;
          version?: number;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "videos_scene_id_fkey";
            columns: ["scene_id"];
            isOneToOne: false;
            referencedRelation: "scenes";
            referencedColumns: ["id"];
          },
        ];
      };
      strategies: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          type: strategy_type;
          parameters: Json;
          enabled: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          name: string;
          type: strategy_type;
          parameters?: Json;
          enabled?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          name?: string;
          type?: strategy_type;
          parameters?: Json;
          enabled?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "strategies_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
        ];
      };
      strategy_signals: {
        Row: {
          id: string;
          strategy_id: string;
          symbol: string;
          signal_type: string;
          price: number | null;
          metadata: Json;
          executed: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          strategy_id: string;
          symbol: string;
          signal_type: string;
          price?: number | null;
          metadata?: Json;
          executed?: boolean;
          created_at?: string;
        };
        Update: {
          id?: string;
          strategy_id?: string;
          symbol?: string;
          signal_type?: string;
          price?: number | null;
          metadata?: Json;
          executed?: boolean;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "strategy_signals_strategy_id_fkey";
            columns: ["strategy_id"];
            isOneToOne: false;
            referencedRelation: "strategies";
            referencedColumns: ["id"];
          },
        ];
      };
      positions: {
        Row: {
          id: string;
          user_id: string;
          symbol: string;
          quantity: number;
          cost_price: number;
          current_price: number | null;
          profit_loss: number | null;
          profit_loss_ratio: number | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          symbol: string;
          quantity: number;
          cost_price: number;
          current_price?: number | null;
          profit_loss?: number | null;
          profit_loss_ratio?: number | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          symbol?: string;
          quantity?: number;
          cost_price?: number;
          current_price?: number | null;
          profit_loss?: number | null;
          profit_loss_ratio?: number | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "positions_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
        ];
      };
      orders: {
        Row: {
          id: string;
          user_id: string;
          position_id: string | null;
          order_id: string | null;
          symbol: string;
          side: order_side;
          quantity: number;
          price: number;
          status: order_status;
          filled_quantity: number;
          filled_price: number | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          position_id?: string | null;
          order_id?: string | null;
          symbol: string;
          side: order_side;
          quantity: number;
          price: number;
          status?: order_status;
          filled_quantity?: number;
          filled_price?: number | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          position_id?: string | null;
          order_id?: string | null;
          symbol?: string;
          side?: order_side;
          quantity?: number;
          price?: number;
          status?: order_status;
          filled_quantity?: number;
          filled_price?: number | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "orders_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "orders_position_id_fkey";
            columns: ["position_id"];
            isOneToOne: false;
            referencedRelation: "positions";
            referencedColumns: ["id"];
          },
        ];
      };
      trades: {
        Row: {
          id: string;
          order_id: string;
          user_id: string;
          trade_id: string | null;
          symbol: string;
          side: order_side;
          quantity: number;
          price: number;
          commission: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          order_id: string;
          user_id: string;
          trade_id?: string | null;
          symbol: string;
          side: order_side;
          quantity: number;
          price: number;
          commission?: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          order_id?: string;
          user_id?: string;
          trade_id?: string | null;
          symbol?: string;
          side?: order_side;
          quantity?: number;
          price?: number;
          commission?: number;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "trades_order_id_fkey";
            columns: ["order_id"];
            isOneToOne: false;
            referencedRelation: "orders";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "trades_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
        ];
      };
      market_data: {
        Row: {
          id: string;
          symbol: string;
          open_price: number | null;
          high_price: number | null;
          low_price: number | null;
          close_price: number | null;
          volume: number | null;
          amount: number | null;
          timestamp: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          symbol: string;
          open_price?: number | null;
          high_price?: number | null;
          low_price?: number | null;
          close_price?: number | null;
          volume?: number | null;
          amount?: number | null;
          timestamp?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          symbol?: string;
          open_price?: number | null;
          high_price?: number | null;
          low_price?: number | null;
          close_price?: number | null;
          volume?: number | null;
          amount?: number | null;
          timestamp?: string;
          created_at?: string;
        };
        Relationships: never[];
      };
      alerts: {
        Row: {
          id: string;
          user_id: string;
          symbol: string;
          condition_type: alert_condition_type;
          condition: Json;
          triggered: boolean;
          triggered_at: string | null;
          message: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          symbol: string;
          condition_type: alert_condition_type;
          condition: Json;
          triggered?: boolean;
          triggered_at?: string | null;
          message?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          symbol?: string;
          condition_type?: alert_condition_type;
          condition?: Json;
          triggered?: boolean;
          triggered_at?: string | null;
          message?: string | null;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "alerts_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
        ];
      };
      backtests: {
        Row: {
          id: string;
          user_id: string;
          strategy_type: strategy_type;
          parameters: Json;
          start_date: string;
          end_date: string;
          initial_capital: number;
          final_capital: number | null;
          total_return: number | null;
          max_drawdown: number | null;
          sharpe_ratio: number | null;
          total_trades: number | null;
          winning_trades: number | null;
          losing_trades: number | null;
          detailed_results: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          strategy_type: strategy_type;
          parameters?: Json;
          start_date: string;
          end_date: string;
          initial_capital: number;
          final_capital?: number | null;
          total_return?: number | null;
          max_drawdown?: number | null;
          sharpe_ratio?: number | null;
          total_trades?: number | null;
          winning_trades?: number | null;
          losing_trades?: number | null;
          detailed_results?: Json | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          strategy_type?: strategy_type;
          parameters?: Json;
          start_date?: string;
          end_date?: string;
          initial_capital?: number;
          final_capital?: number | null;
          total_return?: number | null;
          max_drawdown?: number | null;
          sharpe_ratio?: number | null;
          total_trades?: number | null;
          winning_trades?: number | null;
          losing_trades?: number | null;
          detailed_results?: Json | null;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "backtests_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "users";
            referencedColumns: ["id"];
          },
        ];
      };
      city_policies: {
        Row: {
          id: string;
          city_name: string;
          province_code: string;
          province_name: string;
          peak_price: number;
          valley_price: number;
          flat_price: number;
          peak_hours: string;
          valley_hours: string;
          subsidy_amount: number;
          source_url: string;
          effective_date: string;
          last_verified_at: string | null;
          verification_method: verification_method;
          confidence_score: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          city_name: string;
          province_code: string;
          province_name: string;
          peak_price: number;
          valley_price: number;
          flat_price: number;
          peak_hours: string;
          valley_hours: string;
          subsidy_amount?: number;
          source_url: string;
          effective_date: string;
          last_verified_at?: string | null;
          verification_method?: verification_method;
          confidence_score?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          city_name?: string;
          province_code?: string;
          province_name?: string;
          peak_price?: number;
          valley_price?: number;
          flat_price?: number;
          peak_hours?: string;
          valley_hours?: string;
          subsidy_amount?: number;
          source_url?: string;
          effective_date?: string;
          last_verified_at?: string | null;
          verification_method?: verification_method;
          confidence_score?: number;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: never[];
      };
      policy_monitoring: {
        Row: {
          id: string;
          city_policy_id: string;
          check_type: monitoring_check_type;
          previous_hash: string | null;
          new_hash: string | null;
          change_detected: boolean;
          checked_at: string;
          notes: string | null;
        };
        Insert: {
          id?: string;
          city_policy_id: string;
          check_type: monitoring_check_type;
          previous_hash?: string | null;
          new_hash?: string | null;
          change_detected?: boolean;
          checked_at?: string;
          notes?: string | null;
        };
        Update: {
          id?: string;
          city_policy_id?: string;
          check_type?: monitoring_check_type;
          previous_hash?: string | null;
          new_hash?: string | null;
          change_detected?: boolean;
          checked_at?: string;
          notes?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "policy_monitoring_city_policy_id_fkey";
            columns: ["city_policy_id"];
            isOneToOne: false;
            referencedRelation: "city_policies";
            referencedColumns: ["id"];
          },
        ];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      project_stage: project_stage;
      image_status: image_status;
      video_status: video_status;
      strategy_type: strategy_type;
      order_status: order_status;
      order_side: order_side;
      alert_condition_type: alert_condition_type;
      verification_method: verification_method;
      monitoring_check_type: monitoring_check_type;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
}

// Enum types
export type project_stage = "draft" | "scenes" | "images" | "videos" | "completed";
export type image_status = "pending" | "processing" | "completed" | "failed";
export type video_status = "pending" | "processing" | "completed" | "failed";

// Stock trading enum types
export type strategy_type = "ma" | "macd" | "kdj" | "breakout" | "grid";
export type order_status = "pending" | "submitted" | "partial_filled" | "filled" | "cancelled" | "failed";
export type order_side = "buy" | "sell";
export type alert_condition_type = "price_above" | "price_below" | "volume_spike" | "percent_change" | "indicator";

// Energy storage system enum types
export type verification_method = "manual" | "automated";
export type monitoring_check_type = "scheduled" | "user_report" | "automated";

// Convenience types for tables
export type Project = Database["public"]["Tables"]["projects"]["Row"];
export type ProjectInsert = Database["public"]["Tables"]["projects"]["Insert"];
export type ProjectUpdate = Database["public"]["Tables"]["projects"]["Update"];

export type Scene = Database["public"]["Tables"]["scenes"]["Row"];
export type SceneInsert = Database["public"]["Tables"]["scenes"]["Insert"];
export type SceneUpdate = Database["public"]["Tables"]["scenes"]["Update"];

export type Image = Database["public"]["Tables"]["images"]["Row"];
export type ImageInsert = Database["public"]["Tables"]["images"]["Insert"];
export type ImageUpdate = Database["public"]["Tables"]["images"]["Update"];

export type Video = Database["public"]["Tables"]["videos"]["Row"];
export type VideoInsert = Database["public"]["Tables"]["videos"]["Insert"];
export type VideoUpdate = Database["public"]["Tables"]["videos"]["Update"];

// Combined types for API responses
export type SceneWithMedia = Scene & {
  images: Image[];
  videos: Video[];
};

export type ProjectWithScenes = Project & {
  scenes: SceneWithMedia[];
};

// ============================================================================
// STOCK TRADING TYPES
// ============================================================================

export type Strategy = Database["public"]["Tables"]["strategies"]["Row"];
export type StrategyInsert = Database["public"]["Tables"]["strategies"]["Insert"];
export type StrategyUpdate = Database["public"]["Tables"]["strategies"]["Update"];

export type StrategySignal = Database["public"]["Tables"]["strategy_signals"]["Row"];
export type StrategySignalInsert = Database["public"]["Tables"]["strategy_signals"]["Insert"];
export type StrategySignalUpdate = Database["public"]["Tables"]["strategy_signals"]["Update"];

export type Position = Database["public"]["Tables"]["positions"]["Row"];
export type PositionInsert = Database["public"]["Tables"]["positions"]["Insert"];
export type PositionUpdate = Database["public"]["Tables"]["positions"]["Update"];

export type Order = Database["public"]["Tables"]["orders"]["Row"];
export type OrderInsert = Database["public"]["Tables"]["orders"]["Insert"];
export type OrderUpdate = Database["public"]["Tables"]["orders"]["Update"];

export type Trade = Database["public"]["Tables"]["trades"]["Row"];
export type TradeInsert = Database["public"]["Tables"]["trades"]["Insert"];
export type TradeUpdate = Database["public"]["Tables"]["trades"]["Update"];

export type MarketData = Database["public"]["Tables"]["market_data"]["Row"];
export type MarketDataInsert = Database["public"]["Tables"]["market_data"]["Insert"];
export type MarketDataUpdate = Database["public"]["Tables"]["market_data"]["Update"];

export type Alert = Database["public"]["Tables"]["alerts"]["Row"];
export type AlertInsert = Database["public"]["Tables"]["alerts"]["Insert"];
export type AlertUpdate = Database["public"]["Tables"]["alerts"]["Update"];

export type Backtest = Database["public"]["Tables"]["backtests"]["Row"];
export type BacktestInsert = Database["public"]["Tables"]["backtests"]["Insert"];
export type BacktestUpdate = Database["public"]["Tables"]["backtests"]["Update"];

// Combined types
export type PositionWithOrders = Position & {
  orders: Order[];
};

export type OrderWithTrades = Order & {
  trades: Trade[];
};

export type StrategyWithSignals = Strategy & {
  signals: StrategySignal[];
};

// ============================================================================
// ENERGY STORAGE INVESTMENT DECISION SYSTEM TYPES
// ============================================================================

export type CityPolicy = Database["public"]["Tables"]["city_policies"]["Row"];
export type CityPolicyInsert = Database["public"]["Tables"]["city_policies"]["Insert"];
export type CityPolicyUpdate = Database["public"]["Tables"]["city_policies"]["Update"];

export type PolicyMonitoring = Database["public"]["Tables"]["policy_monitoring"]["Row"];
export type PolicyMonitoringInsert = Database["public"]["Tables"]["policy_monitoring"]["Insert"];
export type PolicyMonitoringUpdate = Database["public"]["Tables"]["policy_monitoring"]["Update"];

// Combined types
export type CityPolicyWithMonitoring = CityPolicy & {
  policy_monitoring: PolicyMonitoring[];
};

// Monitoring types (not in database, used for API responses)
export interface MonitoringSummary {
  total_policies: number;
  fresh_policies: number;
  warning_policies: number;
  stale_policies: number;
  unknown_policies: number;
  needs_verification: CityPolicy[];
}

export interface MonitoringResult {
  checked: number;
  changed: number;
  errors: number;
  results?: Array<{
    city_policy_id: string;
    city_name: string;
    checked: boolean;
    changed: boolean;
    error?: string;
  }>;
}
