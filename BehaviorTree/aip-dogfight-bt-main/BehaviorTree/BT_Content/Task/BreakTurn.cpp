#include "BreakTurn.h"

namespace Action
{
	PortsList BreakTurn::providedPorts()
	{
		return { InputPort<CPPBlackBoard*>("BB") };
	}

	NodeStatus BreakTurn::tick()
	{
		Optional<CPPBlackBoard*> BB = getInput<CPPBlackBoard*>("BB");

		Vector3 my  = (*BB)->MyLocation_Cartesian;
		Vector3 tgt = (*BB)->TargetLocaion_Cartesian;
		Vector3 F = (*BB)->MyForwardVector; F.normalize();
		Vector3 R = (*BB)->MyRightVector;   R.normalize();
		Vector3 U = (*BB)->MyUpVector;      U.normalize();

		// 적기가 내 좌/우 어느 쪽인가 -> 그 방향으로 하드턴
		Vector3 toT = tgt - my;
		double side = (toT.dot(R) >= 0.0) ? 1.0 : -1.0;

		// 전방보다 옆(적 방향)을 크게, 약간 아래로 -> 최대선회 + 코너속도 유지
		(*BB)->VP_Cartesian = my + F * 1000.0 + R * (side * 4000.0) - U * 1500.0;

		return NodeStatus::SUCCESS;
	}
}
